'''
Copyright (c) 2011, Terrence Cole.
All rights reserved.
'''
from melano.hl.types.pyobject import PyObjectType

class Coerce:
	GENERALIZE = 0
	OVERRIDE = 2
	INPLACE = 1


	def __init__(self, coerce_type:int, *children):
		self.coerce_type = coerce_type
		self.children = children
		#self.ll = None


	def get_type(self) -> [type]:
		if self.coerce_type == self.GENERALIZE:
			#TODO: find most general type of children and return that
			return PyObjectType()
		elif self.coerce_type == self.OVERRIDE:
			return self.children[-1].get_type()
		elif self.coerce_type == self.INPLACE:
			return self.children[0].get_type()
		else:
			raise NotImplementedError
