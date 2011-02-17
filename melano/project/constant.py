'''
Copyright (c) 2011, Terrence Cole.
All rights reserved.
'''

class Constant:
	'''Holds a type list of one element.  It is here to be ref'd by Names so that constants in the tree can propogate thier types.'''
	def __init__(self, ty:type):
		self.type = ty
		self.inst = None

	@property
	def types(self) -> [type]:
		return [self.type]

	def create_instance(self, name:str):
		'''
		Instance the type with a name.  Sets the new instance on the 'inst' variable.
		'''
		self.inst = self.type(name)
