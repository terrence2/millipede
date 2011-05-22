'''
Copyright (c) 2011, Terrence Cole
All rights reserved.
'''
from melano.hl.entity import Entity
from melano.hl.name import Name
from melano.hl.scope import Scope
from melano.hl.types.pymodule import PyModuleType
import hashlib
import logging
import tokenize



class MpModule(Scope, Entity):
	'''
	Represents one python-level module.
	'''
	BUILTIN = 0
	STDLIB = 1
	EXTENSION = 2
	PROJECT = 3


	def __init__(self, modtype:int, filename:str, dottedname:str, builtins_scope):
		'''
		The source is the location (project root relative) where
		this module can be found.
		'''
		super().__init__(Name(dottedname, None, None))
		self.owner.scope = self
		self.python_name = dottedname

		# the common builtins scope used by all modules for missing lookups
		self.builtins_scope = builtins_scope

		self.modtype = modtype
		self.filename = filename
		if self.filename.endswith('.py'):
			self.source = self._read_file(self.filename)
			self.checksum = hashlib.sha1(self.source.encode('UTF-8')).hexdigest()
			self.lines = self.source.split('\n')
		else:
			self.source = None
			self.checksum = None
			self.lines = None

		# the ast.Module for this module
		self.ast = None
		self.real_name = None

		# add names common
		#FIXME: the name field of these should be the _name_, not the value... figure out where to put the value
		self.add_symbol('__name__', Name(dottedname, self, None))
		self.add_symbol('__file__', Name(filename, self, None))
		self.add_symbol('__doc__', Name('', self, None))

		# the refs table contains referenced modules (not the symbols they pull in, just a 
		#	mapping from the accessing module name to the module itself).
		self.refs = {}

		# the hl type definition
		self.type = PyModuleType(self)

		# set to true if we are the main module
		self.is_main = False


	def set_as_main(self):
		if self.modtype != MpModule.PROJECT:
			raise SystemError("Main module must be part of the project!")
		self.is_main = True


	#FIXME: are we still using this and should we be?
	@property
	def name(self):
		if self.real_name:
			return self.real_name
		return self.owner.name


	@staticmethod
	def _read_file(filename):
		# read the file contents, obeying the python encoding marker
		with open(filename, 'rb') as fp:
			encoding, _ = tokenize.detect_encoding(fp.readline)
		with open(filename, 'rt', encoding=encoding) as fp:
			content = fp.read()
		content += '\n\n'
		return content


	def lookup(self, name:str) -> Name:
		'''Get the symbol in this scope or raise the lookup to higher scopes by python's rules.'''
		try:
			return self.symbols[name]
		except KeyError:
			return self.builtins_scope.lookup(name)
		raise KeyError(name)


	def has_symbol(self, name:str) -> bool:
		return name in self.symbols


	def get_symbol(self, name:str) -> Name:
		'''Return the symbol from this scope, or raise a KeyError.'''
		return self.symbols[name]


	def lookup_star(self) -> [str]:
		'''Return all of the names exposed by this scope.'''
		#TODO: if we have a static __all__, obey it, rather than giving everything
		#TODO: if __all__ is stored to with a non-const, we need to emit a warning or something
		# Possible strategy: -- copy the file, add a print(__ALL__) to the end, then run it in a real python interpreter
		return list(self.symbols.keys())


	def show(self, level=0):
		logging.info('Module: {} as {}'.format(self.python_name, self.owner.name))
		for name, val in self.symbols.items():
			if isinstance(val.scope, MpModule):
				logging.info('{}Name: {}'.format('\t' * (level + 1), name))
			else:
				val.show(level + 1)


	def get_source_line(self, lineno:int) -> str:
		return self.lines[lineno - 1]


class MpProbedModule(MpModule):
	'''A module with limited functionality because it has no source -- e.g. no ast, unvisitable, etc.'''
	def __init__(self, modtype:int, names:[str], dottedname:str, builtins_scope):
		super().__init__(modtype, '', dottedname, builtins_scope)
		self.symbols = {}
		for name in names:
			self.add_symbol(name, Name(name, self, None))

	def set_as_main(self):
		raise SystemError("Main module must have source!")

	def get_source_line(self, lineno:int) -> str:
		raise SystemError("No source at this line")


class MpMissingModule(MpModule):
	'''A module with limited functionality because we cannot find it when building.  This may be a
		normal, expected condition -- e.g. an import that is simply checking for support that is not expected -- or
		it could be a failure to find a needed module.  We will only know when analyzing if we refer
		to names in the module.  Fail if we lookup a symbol in this module.'''
	QUIRKS = {
			'_emx_link': ['link'],
			'_gestalt': ['gestalt'],
			'_subprocess': ['CREATE_NEW_PROCESS_GROUP', 'CREATE_NEW_CONSOLE'],
			'ce': ['_exit'],
			'hashlib': ['sha512'],
			'java': ['lang'],
			'java.lang': ['System'],
			'org': ['python'],
			'org.python': ['core'],
			'org.python.core': ['PyStringMap'],
			'nt': ['_exit', '_getfullpathname', '_getfileinformation', '_getfinalpathname'],
			'os2': ['_exit'],
			'win32api': ['RegOpenKeyEx', 'RegQueryValueEx', 'GetVersionEx', 'RegCloseKey'],
			'win32con': ['VER_PLATFORM_WIN32_NT', 'VER_PLATFORM_WIN32_WINDOWS', 'HKEY_LOCAL_MACHINE', 'VER_NT_WORKSTATION'],
		}

	def __init__(self, modtype:int, dottedname:str, builtins_scope):
		super().__init__(modtype, '', dottedname, builtins_scope)

		for nm, quirks in self.QUIRKS.items():
			if nm != self.python_name: continue
			for i, quirk in enumerate(quirks):
				self.add_symbol(self.QUIRKS[nm][i], Name(self.QUIRKS[nm][i], self, None), None)


	def lookup(self, name):
		# Note: no need to recurse to builtins, since we can't actually do lookups from _inside_ the module
		return self.symbols[name]


	def lookup_star(self):
		return list(self.symbols.keys())

