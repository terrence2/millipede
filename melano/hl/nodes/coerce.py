'''
Copyright (c) 2011, Terrence Cole.
All rights reserved.
'''
from melano.hl.nodes.entity import Entity
from melano.hl.types.pyobject import PyObjectType


class Coerce(Entity):
	'''Coerce is a generic entity that overrides get_type.  Instead of taking types itself, its type is a
		projection of the types of the children that we create the coercion node with.  add_type on a
		Coerce is invalid.
	'''

	GENERALIZE = 0
	OVERRIDE = 2
	INPLACE = 1
	BOOLEAN = 3


	def __init__(self, coerce_type:int, ast, *children):
		super().__init__(ast)

		for c in children:
			if c is None:
				import pdb; pdb.set_trace()
			assert c is not None

		self.coerce_type = coerce_type
		self.children = children


	def get_display_name(self):
		if self.coerce_type == self.GENERALIZE:
			return 'Coerce-Generalize'
		elif self.coerce_type == self.OVERRIDE:
			return 'Coerce-Override'
		elif self.coerce_type == self.INPLACE:
			return 'Coerce-Inplace'
		elif self.coerce_type == self.BOOLEAN:
			return 'Coerce-Boolean'


	def get_type(self):
		if self.coerce_type == self.GENERALIZE:
			return PyObjectType.common_base([c.get_type() for c in self.children])()
		elif self.coerce_type == self.OVERRIDE:
			return self.children[-1].get_type()
		elif self.coerce_type == self.INPLACE:
			return self.children[0].get_type()
		else:
			raise NotImplementedError


	def add_type(self, ty):
		raise SystemError("Adding a type to a Coerce node is not valid")
