'''
Copyright (c) 2011, Terrence Cole.
All rights reserved.
'''
from melano.c import ast as c
from melano.c.types.lltype import LLType


class CIntegerType(LLType):
	def __init__(self, name, size=None, signed=None, is_a_bool=False):
		super().__init__(name)
		self.size = size
		self.signed = signed
		# allow us to use ints as bools at the C level and still get the right promotion to pyobject later
		self.is_a_bool = is_a_bool


	def declare(self, ctx, quals=[], init=0):
		#TODO: specialize for signed and sized ints
		ctx.add_variable(c.Decl(self.name, c.TypeDecl(self.name, c.IdentifierType('int')), quals=quals, init=c.Constant('integer', init)), False)


	def as_pyobject(self, ctx):
		if self.is_a_bool:
			from melano.c.types.pybool import PyBoolType
			out = PyBoolType(ctx.tmpname())
			out.declare(ctx)
			out._new_from_long(ctx, c.ID(self.name))
			return out
		else:
			from melano.c.types.pyinteger import PyIntegerType
			out = PyIntegerType(ctx.tmpname())
			out.declare(ctx)
			out._new_from_long(ctx, c.ID(self.name))
			return out


	def not_(self, ctx):
		out = CIntegerType(ctx.tmpname())
		out.declare(ctx)
		ctx.add(c.Assignment('=', c.ID(out.name), c.UnaryOp('!', c.ID(self.name))))
		return out
