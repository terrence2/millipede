'''
Copyright (c) 2011, Terrence Cole.
All rights reserved.
'''
from melano.hl.types.pyobject import PyObjectType

class Coerce:
	GENERALIZE = 0

	def __init__(self, coerce_type:int, *children):
		self.coerce_type = coerce_type
		self.children = children
		self.inst = None


	@property
	def type(self):
		return self.types[0]


	@property
	def types(self) -> [type]:
		if self.coerce_type == self.GENERALIZE:
			#TODO: find most general type of children and return that
			return [PyObjectType()]
		else:
			raise NotImplementedError


	def create_instance(self, name:str):
		'''
		Instance the type with a name.  Sets the new instance on the 'inst' variable.
		'''
		self.inst = self.type(name)
