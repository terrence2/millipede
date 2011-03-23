'''
Copyright (c) 2011, Terrence Cole
All rights reserved.
'''
from melano.hl.builtins import Builtins
from melano.hl.name import Name
from melano.hl.scope import Scope
from melano.hl.types.pymodule import PyModuleType
import hashlib
import logging
import tokenize


class MelanoModule(Scope):
	'''
	Represents one python-level module.
	'''
	BUILTIN = 0
	STDLIB = 1
	EXTENSION = 2
	PROJECT = 3


	def __init__(self, modtype:int, filename:str, dottedname:str, builtins_scope:Builtins):
		'''
		The source is the location (project root relative) where
		this module can be found.
		'''
		super().__init__(Name(dottedname.replace('.', '_'), None))

		# the common builtins scope used by all modules for missing lookups
		self.builtins_scope = builtins_scope

		self.modtype = modtype
		self.filename = filename
		if self.filename.endswith('.py'):
			self.source = self.__read_file()
			self.checksum = hashlib.sha1(self.source.encode('UTF-8')).hexdigest()
			self.lines = self.source.split('\n')
		elif self.filename.endswith('.so'):
			self.source = None
			self.checksum = None
			self.lines = None

		# the ast.Module for this module
		self.ast = None

		# add names common
		self.add_symbol('__name__', Name(dottedname, self))
		self.add_symbol('__file__', Name(filename, self))

		# the refs table contains referenced modules (not the symbols they pull in, just a 
		#	mapping from the accessing module name to the module itself).
		self.refs = {}

		# the hl type definition
		self.type = PyModuleType(self)


	def __read_file(self):
		# read the file contents, obeying the python encoding marker
		with open(self.filename, 'rb') as fp:
			encoding, _ = tokenize.detect_encoding(fp.readline)
		with open(self.filename, 'rt', encoding=encoding) as fp:
			content = fp.read()
		content += '\n\n'
		return content


	def lookup(self, name:str) -> Name:
		try:
			return self.symbols[name]
		except KeyError:
			return self.builtins_scope.lookup(name)
		raise KeyError(name)


	def lookup_star(self) -> [str]:
		'''Return all of the names exposed by this scope.'''
		#TODO: if we have a static __all__, obey it, rather than giving everything
		#TODO: if __all__ is stored to with a non-const, we need to emit a warning or something
		# Possible strategy: -- copy the file, add a print(__ALL__) to the end, then run it in a real python interpreter
		return list(self.symbols.keys())


	def show(self, level=0):
		logging.info('Module: {} as {}'.format(self.name, self.owner.global_name))
		for name, val in self.symbols.items():
			if isinstance(val.scope, MelanoModule):
				logging.info('{}Name: {}'.format('\t' * (level + 1), name))
			else:
				val.show(level + 1)


	def get_source_line(self, lineno:int) -> str:
		return self.lines[lineno - 1]

