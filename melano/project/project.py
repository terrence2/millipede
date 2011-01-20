'''
Toplevel tool for analyzing a source base.
'''
from collections import OrderedDict
from melano.parser.driver import PythonParserDriver
from melano.project.module import MelanoModule
from melano.project.passes.find_links import FindLinks
from melano.project.passes.indexer import Indexer
from melano.project.passes.linker import Linker
from copy import copy
import logging
import os
import pickle


class FileNotFoundException(Exception):
	'''Raised when we can't find a referenced module.'''


class MelanoProject:
	'''
	A project represents a collection of python modules.
	
	Starting from a source directory(s) and program(s), this class can
	query the sources to build an information database about a project.
	'''

	def __init__(self, name:str, programs:[str], roots:[str], stdlib:[str], extensions:[str]):
		'''
		The project root(s) is the filesystem path(s) where we should
		start searching for modules in import statements.
		
		The programs list is the set of modules that will be considered
		the project's "main" entry points.
		'''
		self.name = name
		self.programs = programs
		self.roots = roots

		self.stdlib = [os.path.realpath('./data/lib-dynload')] + stdlib
		self.extensions = extensions
		self.builtins = [os.path.realpath('./data/builtins')]
		self.override = [os.path.realpath('./data/override')]

		# maps module paths to module definitions
		self.modules = {} # {str: MelanoModule}
		self.order = []

		# map module names to their path, so we don't have to hit the fs repeatedly 
		self.name_to_path = {} # {str: str}

		# the core parser infrastructure
		self.parser_driver = PythonParserDriver('data/grammar/python-3.1')

		# create a cache directory
		self.cachedir = os.path.realpath('./cache')
		if not os.path.exists(self.cachedir):
			os.makedirs(self.cachedir)

		# list our currently cached entries for fast lookup later
		self.cached = {k: None for k in os.listdir(self.cachedir)}

		# mark uses of the stdlib and builtins in our code for reference
		self.use_stdlib = []
		self.use_builtins = []


	def locate_modules(self):
		'''Perform static, module-level reachability analysis.'''
		logging.info("Name: {}".format(self.name))
		logging.info("Programs: {}".format(self.programs))
		logging.info("Project Roots: {}".format(self.roots))
		logging.info("Stdlib Search: {}".format(self.stdlib))
		logging.info("Extension Search: {}".format(self.extensions))
		logging.info("Builtins Search: {}".format(self.builtins))
		for program in self.programs:
			self._locate_module(program, '')


	def index_names(self):
		'''Find all statically scoped names in reachable modules -- classes, functions, variable, etc.'''
		for fn in self.order:
			mod = self.modules[fn]
			logging.info("Indexing: {}".format(mod.filename))
			indexer = Indexer(self, mod)
			indexer.visit(mod.ast)


	def link_references(self):
		'''Look through our module's reachability and our names databases to find
			the actual definition points for all referenced code.'''
		for fn in self.order:
			mod = self.modules[fn]
			logging.info("Linking: {}".format(mod.filename))
			linker = Linker(self, mod)
			linker.visit(mod.ast)


	def derive_types(self):
		'''Look up-reference and thru-call to find the types of all names.'''


	def find_module(self, dottedname, module):
		return self.modules[self.name_to_path[dottedname]]


	def _locate_module(self, dottedname, contextdir=None, level=0):
		# QUIRK: filter out jython names from the stdlib
		if dottedname.startswith('org.python'):
			return None

		# ensure that all sub-module paths in a dotted name are also loaded and available
		parts = dottedname.split('.')
		for i in range(len(parts)):
			name = '.'.join(parts[0:i + 1])
			mod = self._locate_module_inner(name, contextdir, level)
		return mod


	def _locate_module_inner(self, dottedname, contextdir=None, level=0):
		# locate the module
		logging.debug('locating:{}{}'.format('\t' * level, dottedname))
		progpath = self.__find_module_file(dottedname, contextdir)

		# if we found a module, but it is not one we need to parse, we are done
		if progpath is None:
			return None

		# if we are already loaded, don't reload
		if progpath in self.modules:
			return self.modules[progpath]

		# create the module
		mod = MelanoModule(progpath)
		self.modules[progpath] = mod

		# if we don't have source, make sure the reason is sane
		if not mod.source:
			assert not mod.filename.endswith('.py')
			return mod

		# load the ast
		self.__load_ast(mod)

		# recurse into used modules
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
			return None

		if dottedname[0] != '.' and dottedname in self.name_to_path:
			return self.name_to_path[dottedname]

		# get the base sub-file-name
		fname = os.path.join(*dottedname.split('.'))

		# mod the contextdir by the level
		while dottedname.startswith('.'):
			dottedname = dottedname[1:]
			if dottedname.startswith('.'):
				contextdir = '/'.join(contextdir.split('/')[:-1])
		if not dottedname:
			return None

		# look in the project roots
		path = self.__find_module_in_roots(self.roots, contextdir, dottedname, fname)
		if not path:
			# look in the extensions dir
			path = self.__find_module_in_roots(self.extensions, contextdir, dottedname, fname)
			if not path:
				# look in the stdlib
				path = self.__find_module_in_roots(self.stdlib, contextdir, dottedname, fname)
				if not path:
					# look in the builtins
					path = self.__find_module_in_roots(self.builtins, contextdir, dottedname, fname)
					if not path:
						raise FileNotFoundException(dottedname)

		self.name_to_path[dottedname] = path
		return path


	def __find_module_in_roots(self, baseroots, contextdir, dottedname, filename):
		roots = self.override + copy(baseroots)
		if contextdir:
			roots += [contextdir]

		# query possible filenames names
		for root in roots:
			path = self.__find_module_in_root(root, filename)
			if path:
				return path

		# If we are a dotted name, we may be imported as a module inside the
		# parent.  E.g. when os imports posixpath as path so we can import os.path.
		if '.' in dottedname:
			parts = dottedname.split('.')
			parentname = '.'.join(parts[:-1])
			modfile = self.__find_module_file(parentname, contextdir)
			mod = MelanoModule(modfile)
			self.__load_ast(mod)
			visitor = FindLinks()
			visitor.visit(mod.ast)
			for imp in visitor.imports:
				for alias in imp.names:
					if str(alias.asname) == parts[-1]:
						return self.__find_module_file(str(alias.name))

		return None


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

