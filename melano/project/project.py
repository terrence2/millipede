'''
Copyright (c) 2011, Terrence Cole.
All rights reserved.

Toplevel tool for analyzing a source base.
'''
from melano.c.makefile import Makefile
from melano.c.out import COut
from melano.c.py2c import Py2C
from melano.hl.nodes.builtins import Builtins
from melano.hl.nodes.module import MpModule, MpMissingModule, MpProbedModule
from melano.hl.nodes.name import Name
from melano.project.analysis.clean import Clean
from melano.project.analysis.indexer0 import Indexer0
from melano.project.analysis.indexer1 import Indexer1
from melano.project.analysis.linker import Linker
from melano.project.analysis.typeflow0 import TypeFlow0
from melano.project.global_cache import GlobalCache
from melano.project.importer import Importer, ModuleDesc
from melano.project.project_cache import ProjectCache
from melano.py.driver import PythonParserDriver
import errno
import hashlib
import logging
import melano.py.ast as ast
import os
import pdb
import pickle
import re
import sys


class FileNotFoundException(Exception):
	'''Raised when we can't find a referenced module.'''

class MissingSymbolsError(Exception):
	'''Raised if we cannot resolve all symbols when indexing.'''


class MpProject:
	'''
	A project represents a collection of python modules.
	
	Starting from a source directory(s) and program(s), this class can
	query the sources to build an information database about a project.
	'''

	def __init__(self, name:str, build_dir:str='./build', cache_dir:str='./cache'):
		'''
		The project root(s) is the filesystem path(s) where we should
		start searching for modules in import statements.
		
		The programs list is the set of modules that will be considered
		the project's "main" entry points.
		'''
		self.name = name
		self.build_dir = os.path.realpath(build_dir)
		self.data_dir = os.path.join(os.path.realpath('.'), 'data')

		self.stdlib = [] #[os.path.realpath('./data/lib-dynload')]
		self.extensions = []
		self.builtins = [] #[os.path.realpath('./data/builtins')]
		self.override = [] #[os.path.realpath('./data/override')]

		# defines the c prefix to use when creating the makefile
		self.c_prefix = '/usr'

		# defines the python version postfix and pep3149 abi string that the link target python was built with
		self.c_version = '3.1'
		self.c_abi = ''

		# limit 'local' modules to ones matching 'limit'
		self.limit = re.compile('.*')

		# maps module paths to module definitions
		self.modules_by_path = {} # {str: MpModule}
		self.modules_by_absname = {} # {str: MpModule}
		self.order = [] # depth first traversal order

		# the core parser infrastructure
		self.parser_driver = PythonParserDriver('data/grammar/python-3.1')

		# create a cache directory
		self.cachedir = os.path.realpath('./cache')
		if not os.path.exists(self.cachedir):
			os.makedirs(self.cachedir)

		# ensure the build directory exists
		if not os.path.exists(self.build_dir):
			os.makedirs(self.build_dir)

		# list our currently cached entries for fast lookup later
		self.cache = ProjectCache(name, build_dir, cache_dir)
		self.global_cache = GlobalCache(cache_dir)
		self.cached = {k: None for k in os.listdir(self.cachedir)}

		# build a 'scope' for our builtins
		self.builtins_scope = Builtins(MpModule.BUILTIN, '<builtin>', 'builtins', None)


	def configure(self, *, programs:[str], roots:[str],
				stdlib:[str]=[], extensions:[str]=[], builtins:[str]=[], override:[str]=[],
				prefix:str='/usr', version:str='3.1', abi:str='',
				include='.*', exclude='$^',
				verbose=False, opt_level:int=1, opt_options:{str}=''):
		'''
		Set up this project.
		stdlib, extensions, builtins, overrides : extra directories to search before the standard paths
		builddir : the target build directory
		include : only files matching this regex are part of the program set
		exclude : only files NOT matching this regex are part of the program set
		opt_level : 0 or 1, corresponding to sap and asp respectively
		opt_options : set of string options
			nodocstrings -- elide docstrings from output executable  
		'''
		self.programs = programs
		self.roots = roots
		self.stdlib = stdlib + self.stdlib
		self.extensions = extensions + self.extensions
		self.builtins = builtins + self.builtins
		self.override = override + self.override

		self.c_prefix = prefix
		self.c_version = version
		self.c_abi = abi

		self.limit_include = re.compile(include)
		self.limit_exclude = re.compile(exclude)

		self.opt_level = opt_level
		self.opt_options = opt_options

		self.cache.prepare(programs, roots, stdlib, extensions, builtins, override)

		self.verbose = verbose
		if verbose:
			logging.info("Name: {}".format(self.name))
			logging.info("Programs: {}".format(self.programs))
			logging.info("Project Roots: {}".format(self.roots))
			logging.info("Stdlib Search: {}".format(self.stdlib))
			logging.info("Extension Search: {}".format(self.extensions))
			logging.info("Builtins Search: {}".format(self.builtins))


	def build_all(self):
		self.locate_modules()
		self.index_static()
		self.index_imports()
		self.link_references()
		self.derive_types()
		return self.transform_ll_c()


	def locate_modules(self):
		'''Perform static, module-level reachability analysis.'''
		importer = Importer(self, self.roots, self.stdlib, self.extensions, self.builtins, self.override)

		ref_paths_by_module = {}

		# load all modules in depth-first order
		for program in self.programs:
			importer.trace_import_tree(program)
			#for modname, filename, modtype, ref_paths, ast in reversed(importer.out):
			for desc, ast, ref_paths in reversed(importer.out):
				if desc.type == ModuleDesc.TYPE_MISSING:
					mod = MpMissingModule(desc.modtype, desc.modname, self.builtins_scope)
					assert desc.modname not in self.modules_by_absname
					self.modules_by_absname[desc.modname] = mod

				elif desc.type == ModuleDesc.TYPE_PROBE:
					if desc.modname == 'builtins':
						assert desc.modtype == MpModule.BUILTIN
						mod = self.builtins_scope
					else:
						mod = MpProbedModule(desc.modtype, desc.names, desc.modname, self.builtins_scope)

					assert desc.modname not in self.modules_by_absname
					self.modules_by_absname[desc.modname] = mod

				else:
					assert desc.type == ModuleDesc.TYPE_FILE, "unknown module descriptor type"
					if desc.path in self.modules_by_path:
						logging.warning("Skipping duplicate module: {}".format(desc.path))
						continue
					if self.verbose: logging.info("mapping module: " + desc.modname + ' -> ' + desc.path)

					# create the module
					assert desc.modtype != MpModule.BUILTIN, "we should not have builtin modules with a file"
					mod = MpModule(desc.modtype, desc.path, desc.modname, self.builtins_scope)
					mod.ast = ast
					mod.owner.ast = ast
					mod.ast.hl = mod

					# add to order, in depth first order
					self.order.append(desc.path)

					# map the module by filename
					self.modules_by_path[desc.path] = mod
					self.modules_by_absname[desc.modname] = mod

					# store aside the refmap for after we have loaded all modules
					ref_paths_by_module[desc.path] = ref_paths

					# NOTE: mark each program as having real name __main__
					if desc.modname == program:
						mod.set_as_main()

		# after we have loaded all modules, fill in the refs in each module
		# NOTE: we can only track refs when we have the source (so we know what names are imports)
		for filename, mod in self.modules_by_path.items():
			ref_paths = ref_paths_by_module[filename]
			for local_modname, desc in ref_paths.items():
				try:
					mod.refs[local_modname] = self.modules_by_absname[desc.modname]
				except:
					pdb.set_trace()


	def index_static(self):
		'''Find all statically scoped names in reachable modules -- classes, functions, variable, etc.'''
		logging.info("Indexing: Phase 0, {} files".format(len(self.order)))
		for fn in self.order:
			mod = self.modules_by_path[fn]

			if self.verbose: logging.info("Indexing0: {}".format(mod.filename))
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
		visited = {mod for mod in self.modules_by_absname.values() if isinstance(mod, (MpProbedModule, MpMissingModule))}
		def _index(self):
			nonlocal missing, records, visited
			for fn in reversed(self.order):
				if fn not in missing or missing[fn] > 0:
					mod = self.modules_by_path[fn]
					if self.verbose:
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

				assert self.modules_by_path[fn] in visited or missing[fn] > 0


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
		logging.info("Linking")
		for fn in reversed(self.order):
			mod = self.modules_by_path[fn]
			if self.is_local(mod):
				if self.verbose: logging.info("Linking: {}".format(mod.filename))
				linker = Linker(self, mod)
				linker.visit(mod.ast)


	def derive_types(self):
		'''Look up-reference and thru-call to find the types of all names.'''
		logging.info("Typing")
		for fn in reversed(self.order):
			mod = self.modules_by_path[fn]
			if self.is_local(mod):
				if self.verbose: logging.info("Typing: {}".format(mod.filename))
				typer = TypeFlow0(self, mod)
				typer.visit(mod.ast)


	def transform_ll_c(self):
		makename = 'Makefile-' + (self.programs[0] if len(self.programs) == 1 else hashlib.md5(''.join(self.programs)).hexdigest())
		makefile = Makefile(os.path.join(self.build_dir, makename), self.data_dir, prefix=self.c_prefix, version=self.c_version, abi=self.c_abi)

		for program in self.programs:
			# apply the low-level transformation
			visitor = Py2C(self.opt_level, self.opt_options, self.builtins_scope)
			for fn in self.order:
				mod = self.modules_by_path[fn]
				if self.is_local(mod):
					if self.verbose: logging.info("Preparing: {}".format(mod.filename))
					visitor.preallocate(mod.ast)
			for fn in self.order:
				mod = self.modules_by_path[fn]
				if self.is_local(mod):
					if mod.python_name in self.programs and mod.python_name != program:
						continue
					if self.verbose: logging.info("Emitting: {}".format(mod.filename))
					visitor.visit(mod.ast)
			visitor.close()

			# write the file
			target = os.path.join(self.build_dir, program + '.c')
			logging.info("Writing: {}".format(target))
			with COut(target) as v:
				v.visit(visitor.tu)

			# add us to the makefile
			makefile.add_target(program, target)

			# reset the lowlevel linkage to the now written C structure
			self.reset_ll()
			target = None

		# write the makefile
		makefile.write()

		# link makefile name to Makefile for simplicty
		try:
			os.unlink(os.path.join(self.build_dir, 'Makefile'))
		except OSError as ex:
			if ex.errno != errno.ENOENT: raise
		os.symlink(os.path.join(self.build_dir, makename), os.path.join(self.build_dir, 'Makefile'))

		return makefile


	def reset_ll(self):
		logging.info("Reset LL nodes")

		def _visit_sym(sym):
			sym.ll = None
			if sym.scope:
				_visit_scope(sym.scope)

		def _visit_scope(scope):
			scope.ll = None
			for _, sym in scope.symbols.items():
				if isinstance(sym, Name) and sym.ll:
					_visit_sym(sym)

		for fn in self.order:
			mod = self.modules_by_path[fn]
			if self.is_local(mod):
				_visit_scope(mod)
				v = Clean()
				v.visit(mod.ast)


	def show(self):
		'''Find all statically scoped names in reachable modules -- classes, functions, variable, etc.'''
		logging.info("Showing Project:")
		for fn in self.order:
			mod = self.modules_by_path[fn]
			if self.is_local(mod):
				mod.show()


	def is_local(self, mod:ast.Module) -> bool:
		'''Return true if the module should be translated, false if bridged to.'''
		return (mod.modtype == MpModule.PROJECT and
				self.limit_include.match(mod.filename) is not None and
				self.limit_exclude.match(mod.filename) is None)


	def get_module_at_filename(self, filename):
		return self.modules_by_path[filename]


	def get_module_at_dottedname(self, dottedname):
		return self.modules_by_absname[dottedname]


	def get_file_ast(self, filename):
		source = MpModule._read_file(filename)
		checksum = hashlib.sha1(source.encode('UTF-8')).hexdigest()
		data = self.global_cache.query_ast_data(filename, checksum)

		if data:
			logging.debug("Cached: {} @ {}".format(filename, checksum))
			return pickle.loads(data)

		else:
			logging.info("Parsing: {}".format(filename))
			ast = self.parser_driver.parse_string(source)
			self.global_cache.update_ast_data(filename, checksum, pickle.dumps(ast))
			return ast

