'''
Copyright (c) 2011, Terrence Cole.
All rights reserved.
'''
from melano.hl.types.hltype import HLType


class Constant:
	'''Holds a type list of one element.  It is here to be ref'd by Names so that constants in the tree can propogate thier types.'''
	def __init__(self, ty:HLType):
		self.type = ty
		self.ll = None

		# The attribute map -- we record all potentially attribute usage in the name
		self.attributes = {} # {str: HLType}


	def get_type(self):
		return self.type


	def reference_attribute(self, attr:str):
		self.type.reference_attribute(attr)


	def add_attribute(self, attrname, hltype):
		if attrname not in self.attributes:
			self.attributes[attrname] = []
		if hltype:
			self.attributes[attrname].append(hltype)


	def lookup_attribute(self, attrname):
		return self.attributes[attrname]
