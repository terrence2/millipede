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


	def get_type(self):
		return self.type


	def reference_attribute(self, attr:str):
		self.type.reference_attribute(attr)