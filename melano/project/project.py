'''
Copyright (c) 2011, Terrence Cole.
All rights reserved.

Toplevel tool for analyzing a source base.
'''
from collections import OrderedDict
from copy import copy
from melano.c.out import COut
from melano.c.py2c import Py2C
from melano.c.pybuiltins import PY_BUILTINS
from melano.hl.builtins import Builtins
from melano.hl.module import MelanoModule
from melano.hl.name import Name
from melano.hl.scope import Scope
from melano.project.analysis.find_links import FindLinks
from melano.project.analysis.indexer0 import Indexer0
from melano.project.analysis.indexer1 import Indexer1
from melano.project.analysis.linker import Linker
from melano.project.analysis.typer import Typer
from melano.project.importer import Importer
from melano.py.driver import PythonParserDriver
import hashlib
import logging
import melano.py.ast as ast
import os
import pdb
import pickle
import re


class FileNotFoundException(Exception):
	'''Raised when we can't find a referenced module.'''

class MissingSymbolsError(Exception):
	'''Raised if we cannot resolve all symbols when indexing.'''


class MelanoProject:
	'''
	A project represents a collection of python modules.
	
	Starting from a source directory(s) and program(s), this class can
	query the sources to build an information database about a project.
	'''

	def __init__(self, name:str, programs:[str], roots:[str]):
		'''
		The project root(s) is the filesystem path(s) where we should
		start searching for modules in import statements.
		
		The programs list is the set of modules that will be considered
		the project's "main" entry points.
		'''
		self.name = name
		self.programs = {p: None for p in programs}
		self.roots = roots
		self.build_dir = os.path.realpath('./build')

		self.stdlib = [os.path.realpath('./data/lib-dynload')]
		self.extensions = []
		self.builtins = [os.path.realpath('./data/builtins')]
		self.override = [os.path.realpath('./data/override')]

		# limit 'local' modules to ones matching 'limit'
		self.limit = re.compile('.*')

		# maps module paths to module definitions
		self.modules_by_path = {} # {str: MelanoModule}
		self.modules_by_absname = {} # {str: MelanoModule}
		self.order = [] # depth first traversal order

		# map module names to their path and type, so we don't have to hit the fs repeatedly 
		#self.name_to_path = {} # {str: str}
		#self.name_to_type = {} # {str: int}

		# the core parser infrastructure
		self.parser_driver = PythonParserDriver('data/grammar/python-3.1')

		# create a cache directory
		self.cachedir = os.path.realpath('./cache')
		if not os.path.exists(self.cachedir):
			os.makedirs(self.cachedir)

		# list our currently cached entries for fast lookup later
		self.cached = {k: None for k in os.listdir(self.cachedir)}

		# build a 'scope' for our builtins
		self.builtins_scope = Builtins(Name('builtins', None))
		for n in PY_BUILTINS:
			self.builtins_scope.add_symbol(n)


	def configure(self, *, stdlib:[str]=[], extensions:[str]=[], builtins:[str]=[], override:[str]=[], builddir='./build',
				limit='.*', verbose=False):
		'''
		Set up this project.
		stdlib, extensions, builtins, overrides : extra directories to search before the standard paths
		builddir : the target build directory
		limit : only files matching this regex as part of the program set
		'''
		self.stdlib = stdlib + self.stdlib
		self.extensions = extensions + self.extensions
		self.builtins = builtins + self.builtins
		self.override = override + self.override

		self.build_dir = os.path.realpath(builddir)
		self.limit = re.compile(limit)

		self.verbose = verbose
		if verbose:
			logging.info("Name: {}".format(self.name))
			logging.info("Programs: {}".format(self.programs))
			logging.info("Project Roots: {}".format(self.roots))
			logging.info("Stdlib Search: {}".format(self.stdlib))
			logging.info("Extension Search: {}".format(self.extensions))
			logging.info("Builtins Search: {}".format(self.builtins))


	def build(self, target):
		self.locate_modules()
		self.index_static()
		self.index_imports()
		self.link_references()
		self.derive_types()
		if target.endswith('.c'):
			c = self.transform_lowlevel_c()
			logging.info("Writing: {}".format(target))
			with COut(target) as v:
				v.visit(c)
		else:
			raise NotImplementedError('target must be a c file at the moment')


	def locate_modules(self):
		'''Perform static, module-level reachability analysis.'''
		importer = Importer(self, self.roots, self.stdlib, self.extensions, self.builtins, self.override)

		ref_paths_by_module = {}

		# load all modules in depth-first order
		for program in self.programs:
			importer.trace_import_tree(program)
			for modname, filename, modtype, ref_paths in reversed(importer.out):
				if filename in self.modules_by_path:
					continue
				logging.info("mapping module: " + modname + ' -> ' + filename)
				# create the module
				mod = MelanoModule(modtype, filename, modname, self.builtins_scope)
				# add to order, in depth first order
				self.order.append(filename)
				# map the module by filename
				self.modules_by_path[filename] = mod
				# load the (already cached) ast into the module struct and backref it
				if filename.endswith('.py'):
					self.__load_ast(mod)
					mod.ast.hl = mod
				# store aside the refmap for after we have loaded all modules
				ref_paths_by_module[filename] = ref_paths

				# NOTE: mark each program as having real name __main__
				if modname == program:
					mod.set_as_main()

		# after we have loaded all modules, fill in the refs in each module
		for filename, mod in self.modules_by_path.items():
			ref_paths = ref_paths_by_module[filename]
			for local_modname, ref_filename in ref_paths.items():
				mod.refs[local_modname] = self.modules_by_path[ref_filename]


	def index_static(self):
		'''Find all statically scoped names in reachable modules -- classes, functions, variable, etc.'''
		logging.info("Indexing: Phase 0, {} files".format(len(self.order)))
		for fn in self.order:
			mod = self.modules_by_path[fn]
			logging.info("Indexing0: {}".format(mod.filename))
			indexer = Indexer0(self, mod)
			indexer.visit(mod.ast)

			# NOTE: we may need to visit twice (but only twice) because of a nonlocal declared before its target
			if indexer.missing:
				indexer = Indexer0(self, mod)
				indexer.visit(mod.ast)
				assert not indexer.missing, 'Missing symbols: {}'.format(indexer.missing)


	def index_imports(self):
		'''Find and add to the scope stack, all names from imports.'''
		missing = {}
		records = {}
		visited = set()
		def _index(self):
			nonlocal missing, records, visited
			for fn in self.order:
				if fn not in missing or missing[fn] > 0:
					mod = self.modules_by_path[fn]
					if fn not in missing:
						logging.info("Indexing1: {}".format(mod.filename))
					else:
						logging.info("[{} remaining] Indexing1: {}".format(sum(list(missing.values())), fn))
					indexer = Indexer1(self, mod, visited)
					indexer.visit(mod.ast)
					missing[fn] = len(indexer.missing)
					records[fn] = indexer.missing
					if 0 == missing[fn]:
						visited.add(mod)

		logging.info("Indexing: Phase 1, {} files".format(len(self.order)))
		_index(self)

		logging.info("Indexing: Phase 2, {} remaining".format(sum(list(missing.values()))))
		while sum(list(missing.values())) > 0:
			prior = sum(list(missing.values()))
			_index(self)
			cur = sum(list(missing.values()))
			if cur == prior:
				raise MissingSymbolsError({fn: sym for fn, sym in records.items() if len(sym) > 0})


	def link_references(self):
		'''Look through our module's reachability and our names databases to find
			the actual definition points for all referenced code.'''
		for fn in self.order:
			mod = self.modules_by_path[fn]
			if self.is_local(mod):
				logging.info("Linking: {}".format(mod.filename))
				linker = Linker(self, mod)
				linker.visit(mod.ast)


	def derive_types(self):
		'''Look up-reference and thru-call to find the types of all names.'''
		for fn in self.order:
			mod = self.modules_by_path[fn]
			if self.is_local(mod):
				logging.info("Typing: {}".format(mod.filename))
				typer = Typer(self, mod)
				typer.visit(mod.ast)


	def transform_lowlevel_c(self):
		visitor = Py2C()
		for mod in self.modules_by_path.values():
			if self.is_local(mod):
				logging.info("Preparing: {}".format(mod.filename))
				visitor.preallocate(mod.ast)
		for fn in self.order:
			mod = self.modules_by_path[fn]
			if self.is_local(mod):
				logging.info("Emitting: {}".format(mod.filename))
				visitor.visit(mod.ast)
		visitor.close()

		return visitor.tu


	def show(self):
		'''Find all statically scoped names in reachable modules -- classes, functions, variable, etc.'''
		logging.info("Showing Project:")
		for fn in self.order:
			mod = self.modules_by_path[fn]
			if self.is_local(mod):
				mod.show()


	def is_local(self, mod:ast.Module) -> bool:
		'''Return true if the module should be translated, false if bridged to.'''
		return mod.modtype == MelanoModule.PROJECT and self.limit.match(mod.filename) is not None


	def get_file_ast(self, filename):
		source = MelanoModule._read_file(filename)
		checksum = hashlib.sha1(source.encode('UTF-8')).hexdigest()
		cachefile = os.path.join(self.cachedir, checksum)
		if checksum in self.cached:
			logging.debug("Cached: {}".format(filename))
			with open(cachefile, 'rb') as fp:
				ast = pickle.load(fp)
		else:
			logging.info("Parsing: {}".format(filename))
			ast = self.parser_driver.parse_string(source)
			with open(cachefile, 'wb') as fp:
				pickle.dump(ast, fp, pickle.HIGHEST_PROTOCOL)
				self.cached[checksum] = True
		return ast


	def __load_ast(self, mod):
		'''Find the ast for this module.'''
		cachefile = os.path.join(self.cachedir, mod.checksum)
		if mod.checksum in self.cached:
			logging.debug("Cached: {}".format(mod.filename))
			with open(cachefile, 'rb') as fp:
				mod.ast = pickle.load(fp)
		else:
			logging.info("Parsing: {}".format(mod.filename))
			mod.ast = self.parser_driver.parse_string(mod.source)
			with open(cachefile, 'wb') as fp:
				pickle.dump(mod.ast, fp, pickle.HIGHEST_PROTOCOL)
				self.cached[mod.checksum] = True
