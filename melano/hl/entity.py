'''
Copyright (c) 2011, Terrence Cole.
All rights reserved.
'''

class Entity:
	'''
	A 'thing' in the program that is usable in the standard ways.  E.g. attribute access, indexing, etc.
	'''
	def __init__(self):
		super().__init__()

		# The attribute map -- we record all potential attribute usage in the name
		self.attributes = {} # {str: HLType}

		# The subscript map -- we record all potential indexing of this name here
		self.subscripts = {} # {slice: HLType}


	def add_attribute(self, attrname, hltype):
		if attrname not in self.attributes:
			self.attributes[attrname] = []
		if hltype:
			self.attributes[attrname].append(hltype)


	def add_subscript(self, slice, hltype):
		if slice not in self.subscripts:
			self.subscripts[slice] = []
		if hltype:
			self.subscripts[slice].append(hltype)


	def lookup_attribute(self, attrname):
		return self.attributes[attrname]

