'''
Toplevel tool for analyzing a source base.
'''
from melano.parser.driver import PythonParserDriver
from melano.project.module import MelanoModule
from melano.project.passes.find_links import FindLinks
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
	BUILTINS = ['_functools']

	def __init__(self, name:str, roots:[str], programs:[str]):
		'''
		The project root(s) is the filesystem path(s) where we should
		start searching for modules in import statements.
		
		The programs list is the set of modules that will be considered
		the project's "main" entry points.
		'''
		self.name = name
		self.roots = roots + [os.path.realpath('./data/builtins')]
		self.programs = programs
		self.modules = {}

		self.parser_driver = PythonParserDriver('data/grammar/python-3.1')

		# create a cache directory
		self.cachedir = os.path.realpath('./cache')
		if not os.path.exists(self.cachedir):
			os.makedirs(self.cachedir)

		# list our currently cached entries for fast lookup later
		self.cached = {k: None for k in os.listdir(self.cachedir)}


	def locate_modules(self):
		for program in self.programs:
			self._locate_module(program, '')


	def _locate_module(self, dottedname, contextdir=None, level=0):
		# QUIRK: filter out jython names from the stdlib
		if dottedname.startswith('org.python'):
			return None

		# locate the module
		logging.info('locating:' + '\t' * level + dottedname)
		progpath = self.__find_module_file(dottedname, contextdir)
		if progpath in self.modules:
			return self.modules[progpath]

		# create the module
		mod = MelanoModule(progpath)
		self.modules[progpath] = mod

		# if we have the source for the module, load it up
		if mod.source:
			self.__load_ast(mod)
			for dname, (_entry, _asname) in self.__find_outbound_links(mod):
				contextdir = os.path.dirname(mod.filename)
				submod = self._locate_module(dname, contextdir, level + 1)
				mod.refs.append(submod)
				#if entry:
				#	# TODO: lookup entry in module and assign to namespace under asname
				#	mod.ns[asname] = None
				#else:
				#	mod.ns[dname] = submod
		return mod


	def __find_module_file(self, dottedname, contextdir=None):
		'''Given a dotted name, locate the file that should contain the module's 
			code.  This will look relative to the roots, and contextdir, if set.'''
		# get the base sub-file-name
		fname = os.path.join(*dottedname.split('.'))

		# mod the contextdir by the level
		while dottedname.startswith('.'):
			dottedname = dottedname[1:]
			if dottedname.startswith('.'):
				contextdir = '/'.join(contextdir.split('/')[:-1])

		# figure out where to look
		roots = self.roots
		if contextdir:
			roots += [contextdir]

		# query possible names in each root
		for root in roots:
			path = os.path.join(root, fname)

			# try package module or normal module
			if os.path.isdir(path):
				tst = os.path.join(path, '__init__.py')
				if os.path.isfile(tst):
					return tst
			else:
				tst = path + '.py'
				if os.path.isfile(tst):
					return tst

			# try c modules
			path = path + '.so'
			if os.path.isfile(path) or os.path.islink(path):
				return path

		# If we are a dotted name, we may be imported as a module inside the
		# parent.  E.g. when os imports posixpath as path so we can import os.path.
		if '.' in dottedname:
			parts = dottedname.split('.')
			modfile = self.__find_module_file('.'.join(parts[:-1]), contextdir)
			mod = MelanoModule(modfile)
			self.__load_ast(mod)
			visitor = FindLinks()
			visitor.visit(mod.ast)
			for imp in visitor.imports:
				for alias in imp.names:
					if str(alias.asname) == parts[-1]:
						return self.__find_module_file(str(alias.name))


		raise FileNotFoundException(dottedname)


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

