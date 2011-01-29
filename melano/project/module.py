'''
Copyright (c) 2011, Terrence Cole
All rights reserved.
'''
from melano.project.builtin import lookup_builtin
from melano.project.type.object import PyObject
from melano.project.type.ptr import Ptr
import hashlib
import tokenize


class MelanoModule:
	'''
	Represents one python-level module.
	'''
	BUILTIN = 0
	STDLIB = 1
	EXTENSION = 2
	PROJECT = 3

	def __init__(self, modtype:int, filename:str):
		'''
		The source is the location (project root relative) where
		this module can be found.
		'''
		self.type = modtype
		self.filename = filename
		if self.filename.endswith('.py'):
			self.source = self.__read_file()
			self.checksum = hashlib.sha1(self.source.encode('UTF-8')).hexdigest()
		elif self.filename.endswith('.so'):
			self.source = None
			self.checksum = None

		# module-specific fields
		self.ast = None
		self.refs = {} # {ast.Attribute or ast.Name: MelanoModule}

		# common fields for all namespace entries
		self.parent = None # always nil for modules
		self.names = {
					'__file__': filename
					}


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


	def lookup(self, name):
		'''Query for a name.  Overflow into module builtins.'''
		if name in self.names:
			return self.names[name]
		#import pdb;pdb.set_trace()
		ref = lookup_builtin(name)
		if ref is not None:
			return ref
		raise KeyError(name)


	def get_type(self):
		'''FIXME: this should depend on whether we are loaded from py, and local or not.'''
		return Ptr(PyObject())

	def __str__(self):
		return '<Module[{}]>'.format(self.names.get('__name__', self.filename))

