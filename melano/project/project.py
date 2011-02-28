'''
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
from melano.project.analysis.coder import Coder
from melano.project.analysis.find_links import FindLinks
from melano.project.analysis.indexer import Indexer
from melano.project.analysis.linker import Linker
from melano.project.analysis.typer import Typer
from melano.py.driver import PythonParserDriver
import logging
import melano.py.ast as ast
import os
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

		self.stdlib = [os.path.realpath('./data/lib-dynload'), '/usr/lib/python3.1', '/usr/lib/python3.1/lib-dynload']
		self.extensions = ['/usr/lib/python3.1/site-packages']
		self.builtins = [os.path.realpath('./data/builtins')]
		self.override = [os.path.realpath('./data/override')]

		# limit 'local' modules to ones matching 'limit'
		self.limit = re.compile('.*')

		# maps module paths to module definitions
		self.modules = {} # {str: MelanoModule}
		self.order = []

		# map module names to their path and type, so we don't have to hit the fs repeatedly 
		self.name_to_path = {} # {str: str}
		self.name_to_type = {} # {str: int}

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
		self.index_names()
		self.show()
		self.link_references()
		self.derive_types()
		self.show()
		if target.endswith('.c'):
			c = self.transform_lowlevel_c()
			with COut('test.c') as v:
				v.visit(c)
		else:
			raise NotImplementedError('target must be a c file at the moment')


	def locate_modules(self):
		'''Perform static, module-level reachability analysis.'''
		for program in self.programs:
			mod = self._locate_module(program, '', is_main=True)
			self.programs[program] = mod


	def index_names(self):
		'''Find all statically scoped names in reachable modules -- classes, functions, variable, etc.'''
		missing = {}
		def _index(self):
			for fn in self.order:
				if fn not in missing or missing[fn] > 0:
					mod = self.modules[fn]
					if fn not in missing:
						logging.info("Indexing: {}".format(mod.filename))
					else:
						logging.info("[{} remaining] Indexing: {}".format(sum(list(missing.values())), fn))
					indexer = Indexer(self, mod)
					indexer.visit(mod.ast)
					if self.is_local(mod):
						missing[fn] = len(indexer.missing)

		logging.info("Indexing: Phase 1, {} files".format(len(self.order)))
		_index(self)

		logging.info("Indexing: Phase 2, {} remaining".format(sum(list(missing.values()))))
		while sum(list(missing.values())) > 0:
			prior = sum(list(missing.values()))
			_index(self)
			cur = sum(list(missing.values()))
			if cur == prior:
				raise MissingSymbolsError



	def link_references(self):
		'''Look through our module's reachability and our names databases to find
			the actual definition points for all referenced code.'''
		for fn in self.order:
			mod = self.modules[fn]
			if self.is_local(mod):
				logging.info("Linking: {}".format(mod.filename))
				linker = Linker(self, mod)
				linker.visit(mod.ast)


	def derive_types(self):
		'''Look up-reference and thru-call to find the types of all names.'''
		for fn in self.order:
			mod = self.modules[fn]
			if self.is_local(mod):
				logging.info("Typing: {}".format(mod.filename))
				typer = Typer(self, mod)
				typer.visit(mod.ast)


	def transform_lowlevel_c(self):
		visitor = Py2C()
		for mod in self.modules.values():
			if self.is_local(mod):
				visitor.visit(mod.ast)
		visitor.close()
		return visitor.tu




	def emit_code(self):
		'''Look up-reference and thru-call to find the types of all names.'''
		m = Makefile(self.build_dir, self.roots)
		for fn in self.order:
			mod = self.modules[fn]
			if self.is_local(mod):
				logging.info("Emit: {}".format(mod.filename))
				if mod.names['__name__'] != '__main__':
					tgt = m.add_source(mod.filename)
					v = Coder(self, mod, tgt)
					v.visit(mod.ast)
					tgt.emit()
					tgt.close()

		for program in self.programs:
			mod = self.programs[program]
			tgt = m.add_program(program, mod.filename)
			v = Coder(self, mod, tgt)
			v.visit(mod.ast)
			tgt.set_entry(v.context.name)
			tgt.emit()
			tgt.close()

		m.write()



	def show(self):
		'''Find all statically scoped names in reachable modules -- classes, functions, variable, etc.'''
		logging.info("Showing Project:")
		for fn in self.order:
			mod = self.modules[fn]
			if self.is_local(mod):
				mod.show()



	def find_module(self, dottedname, module):
		return self.modules[self.name_to_path[dottedname]]


	def is_local(self, mod:ast.Module) -> bool:
		'''Return true if the module should be translated, false if bridged to.'''
		return mod.modtype == MelanoModule.PROJECT and self.limit.match(mod.filename) is not None


	def __name_for_module_path(self, path):
		'''Map backwards from a path to a canonical name.  A module may be loaded under
			many different paths and in many different ways, even through its import and
			rename in another module.'''
		paths = self.roots + self.stdlib + self.extensions + self.builtins + self.override
		paths.sort(key=lambda p: len(p.split('/')))
		for base in reversed(paths):
			if path.startswith(base):
				path = path[len(base) + 1:]
				path = os.path.splitext(path)[0]
				path = path.replace('/', '.')
				return path


	def _locate_module(self, dottedname, contextdir=None, level=0, is_main=False):
		# QUIRK: filter out jython names from the stdlib
		if dottedname.startswith('org.python'):
			return None

		# ensure that all sub-module paths in a dotted name are also loaded and available
		parts = dottedname.split('.')
		for i in range(len(parts)):
			name = '.'.join(parts[0:i + 1])
			mod = self._locate_module_inner(name, contextdir, level, is_main)
		return mod


	def _locate_module_inner(self, dottedname, contextdir=None, level=0, is_main=False):
		# locate the module
		logging.debug('locating:{}{}'.format('\t' * level, dottedname))
		modtype, progpath = self.__find_module_file(dottedname, contextdir)

		# if we found a module, but it is not one we need to parse, we are done
		if progpath is None:
			return None

		# if we are already loaded, don't reload
		if progpath in self.modules:
			return self.modules[progpath]

		# create the module
		mod = MelanoModule(modtype, progpath, dottedname if not is_main else '__main__', self.builtins_scope)
		mod.name = self.__name_for_module_path(progpath)
		self.modules[progpath] = mod

		# if we don't have source, make sure the reason is sane
		if not mod.source:
			assert not mod.filename.endswith('.py')
			return mod

		# load the ast
		self.__load_ast(mod)
		mod.ast.hl = mod

		# recurse into used modules
		if self.is_local(mod):
			for dname, (_entry, _asname) in self.__find_outbound_links(mod):
				contextdir = os.path.dirname(mod.filename)
				submod = self._locate_module(dname, contextdir, level + 1)
				mod.refs[dname] = submod

		self.order.append(mod.filename)
		return mod


	def __find_module_file(self, dottedname, contextdir=None):
		'''Given a dotted name, locate the file that should contain the module's 
			code.  This will look relative to the roots, and contextdir, if set.'''
		if not dottedname:
			return None, None

		if dottedname[0] != '.' and dottedname in self.name_to_path:
			return self.name_to_type[dottedname], self.name_to_path[dottedname]

		# get the base sub-file-name
		fname = os.path.join(*dottedname.split('.'))

		# mod the contextdir by the level
		while dottedname.startswith('.'):
			dottedname = dottedname[1:]
			if dottedname.startswith('.'):
				contextdir = '/'.join(contextdir.split('/')[:-1])
		if not dottedname:
			return None, None

		# look in the project roots
		modtype = MelanoModule.PROJECT
		rec_modtype, path = self.__find_module_in_roots(self.roots, contextdir, dottedname, fname)
		if not path:
			# look in the extensions dir
			modtype = MelanoModule.EXTENSION
			rec_modtype, path = self.__find_module_in_roots(self.extensions, contextdir, dottedname, fname)
			if not path:
				# look in the stdlib
				modtype = MelanoModule.STDLIB
				rec_modtype, path = self.__find_module_in_roots(self.stdlib, contextdir, dottedname, fname)
				if not path:
					# look in the builtins
					modtype = MelanoModule.BUILTIN
					rec_modtype, path = self.__find_module_in_roots(self.builtins, contextdir, dottedname, fname)
					if not path:
						raise FileNotFoundException(dottedname)

		# if we loaded recursively and got a modtype, set it, not the highlevel discovered type
		if rec_modtype >= 0: modtype = rec_modtype

		self.name_to_type[dottedname] = modtype
		self.name_to_path[dottedname] = path
		return modtype, path


	def __find_module_in_roots(self, baseroots, contextdir, dottedname, filename):
		roots = self.override + copy(baseroots)
		if contextdir and contextdir not in roots:
			roots += [contextdir]

		# query possible filenames names
		for root in roots:
			path = self.__find_module_in_root(root, filename)
			if path:
				return - 1, path

		# If we are a dotted name, we may be imported as a module inside the
		# parent.  E.g. when os imports posixpath as path so we can import os.path.
		if '.' in dottedname:
			parts = dottedname.split('.')
			parentname = '.'.join(parts[:-1])
			modtype, modfile = self.__find_module_file(parentname, contextdir)
			mod = MelanoModule(modtype, modfile, parentname, self.builtins_scope)
			self.__load_ast(mod)
			visitor = FindLinks()
			visitor.visit(mod.ast)
			for imp in visitor.imports:
				for alias in imp.names:
					if str(alias.asname) == parts[-1]:
						modtype, path = self.__find_module_file(str(alias.name))
						return modtype, path

		return None, None


	def __find_module_in_root(self, root, filename):
		path = os.path.join(root, filename)

		# try package module or normal module
		if os.path.isdir(path):
			tst = os.path.join(path, '__init__.py')
			if os.path.isfile(tst):
				return tst
		else:
			tst = path + '.py'
			if os.path.isfile(tst):
				return tst

		tst = path + '.so'
		if os.path.isfile(tst):
			logging.critical("Using SO: {}".format(tst))
			return tst

		return None


	def __load_ast(self, mod):
		'''Find the ast for this module.'''
		cachefile = os.path.join(self.cachedir, mod.checksum)
		if mod.checksum in self.cached:
			logging.info("Cached: {}".format(mod.filename))
			with open(cachefile, 'rb') as fp:
				mod.ast = pickle.load(fp)
		else:
			logging.info("Parsing: {}".format(mod.filename))
			mod.ast = self.parser_driver.parse_string(mod.source)
			with open(cachefile, 'wb') as fp:
				pickle.dump(mod.ast, fp, pickle.HIGHEST_PROTOCOL)


	def __find_outbound_links(self, mod):
		visitor = FindLinks()
		visitor.visit(mod.ast)
		for imp in visitor.imports:
			for alias in imp.names:
				modname = str(alias.name)
				asname = str(alias.asname) if alias.asname else modname
				yield modname, (None, asname)
		for imp in visitor.importfroms:
			module = '.' * imp.level + str(imp.module)
			for alias in imp.names:
				name = str(alias.name)
				asname = str(alias.asname) if alias.asname else name
				yield module, (name, asname)

