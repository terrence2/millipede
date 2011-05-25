'''
Copyright (c) 2011, Terrence Cole.
All rights reserved.
'''
from melano.hl.nodes.entity import Entity
from melano.hl.types.pyobject import PyObjectType


class Attribute(Entity):
	'''Describes an access (without a direct name), to an attribute value of another node..
	This is always tagged onto the hl property of an Attribute ast node.  It can hold one
	Entity on the left and a Name on the right.

	This does not store the type info directly; in order to get type info, it inspects the lhs Entity
	using the value provided by the rhs.
	'''
	def __init__(self, lhs:Entity, rhs:str, ast):
		super().__init__(ast)
		self.lhs = lhs
		self.rhs = rhs


	def get_type(self):
		#TODO: lookup whatever slice_ast represents in base
		return PyObjectType()
