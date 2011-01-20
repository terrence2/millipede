'''
Copyright (c) 2011, Terrence Cole
All rights reserved.
'''
import tokenize
import hashlib


class MelanoModule:
	'''
	Represents one python-level module.
	'''
	def __init__(self, filename:str):
		'''
		The source is the location (project root relative) where
		this module can be found.
		'''
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
		self.names = {}


	def __read_file(self):
		# read the file contents, obeying the python encoding marker
		with open(self.filename, 'rb') as fp:
			encoding, _ = tokenize.detect_encoding(fp.readline)
		with open(self.filename, 'rt', encoding=encoding) as fp:
			content = fp.read()
		content += '\n\n'
		return content


	def lookup_name(self, name):
		return self.names[name]


	def lookup_star(self):
		return self.names

