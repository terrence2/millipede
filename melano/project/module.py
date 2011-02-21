'''
Copyright (c) 2011, Terrence Cole
All rights reserved.
'''
from melano.c.types.lltype import LLType
from melano.c.types.pymodule import PyModuleType
from melano.project.name import Name
from melano.project.scope import Scope
import hashlib
import tokenize



class MelanoModule(Scope):
	'''
	Represents one python-level module.
	'''
	BUILTIN = 0
	STDLIB = 1
	EXTENSION = 2
	PROJECT = 3


	def __init__(self, modtype:int, filename:str, dottedname:str):
		'''
		The source is the location (project root relative) where
		this module can be found.
		'''
		super().__init__(Name(dottedname.replace('.', '_'), None))

		self.modtype = modtype
		self.filename = filename
		if self.filename.endswith('.py'):
			self.source = self.__read_file()
			self.checksum = hashlib.sha1(self.source.encode('UTF-8')).hexdigest()
		elif self.filename.endswith('.so'):
			self.source = None
			self.checksum = None
		self.lines = None

		# the ast.Module for this module
		self.ast = None

		# add names common
		self.add_symbol('__name__', dottedname)
		self.add_symbol('__file__', filename)

		# the refs table contains referenced modules (not the symbols they pull in, just a 
		#	mapping from the accessing module name to the module itself).
		self.refs = {}


	def __read_file(self):
		# read the file contents, obeying the python encoding marker
		with open(self.filename, 'rb') as fp:
			encoding, _ = tokenize.detect_encoding(fp.readline)
		with open(self.filename, 'rt', encoding=encoding) as fp:
			content = fp.read()
		content += '\n\n'
		return content


	def lookup_name(self, name):
		'''Query the name list for an existing reference.'''
		return self.names[name]


	def lookup_star(self):
		return self.names


	def show(self, level=0):
		print(self.owner.name)
		super().show(level)


	def get_source_line(self, lineno:int) -> str:
		if self.lines is None:
			self.lines = self.source.split('\n')
		return self.lines[lineno - 1]


	"""
	def lookup(self, name):
		'''Query for a name.  Overflow into module builtins.'''
		if name in self.names:
			return self.names[name]
		ref = lookup_builtin(name)
		if ref is not None:
			return ref
		raise KeyError(name)



	def __str__(self):
		return '<Module[{}]>'.format(self.names.get('__name__', self.filename))
	"""
