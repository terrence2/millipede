'''
Copyright (c) 2011, Terrence Cole.
All rights reserved.
'''
from melano.hl.nodes.entity import Entity
from melano.hl.types.pyobject import PyObjectType


class Subscript(Entity):
	'''Describes an access, however, unlike name it doesn't have a name.
	This is always tagged onto the hl property of a Subscript ast node.  It can hold one of:
		Index(Tuple or Num or Expr), Ellipsis, Slice, or ExtSlice
	The base is the hl node of the thing that we are subscripting.  In order to get the type
	of this particular subscript, we do a lookup on the base node's Entity properties based on
	our specific ast.
	'''
	def __init__(self, base, slice_ast, ast):
		super().__init__(ast)
		self.base = base
		self.slice_ast = slice_ast


	def get_type(self):
		#TODO: lookup whatever slice_ast represents in base
		return PyObjectType()
