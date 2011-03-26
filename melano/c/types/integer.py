'''
Copyright (c) 2011, Terrence Cole.
All rights reserved.
'''
from melano.c import ast as c
from melano.c.types.lltype import LLType
from melano.hl.types.hltype import HLType


class CIntegerLL(LLType):
	def __init__(self, hlnode, visitor, size=None, signed=None, is_a_bool=False):
		super().__init__(hlnode, visitor)
		self.size = self.hltype.size if self.hltype else size
		self.signed = self.hltype.signed if self.hltype else signed
		# allow us to use ints as bools at the C level and still get the right promotion to pyobject later
		self.is_a_bool = self.hltype.is_a_bool if self.hltype else is_a_bool


	def declare(self, ctx, quals=[], init=0, name=None):
		super().declare(ctx, quals, name)
		#TODO: specialize for signed and sized ints
		ctx.add_variable(c.Decl(self.name, c.TypeDecl(self.name, c.IdentifierType('int')), quals=quals, init=c.Constant('integer', init)), False)


	def as_pyobject(self, ctx):
		if self.is_a_bool:
			out = PyBoolLL(None, self.visitor)
			out.declare(self.visitor.scope.context)
			out._new_from_long(ctx, c.ID(self.name))
			return out
		else:
			out = PyIntegerLL(None, self.visitor)
			out.declare(self.visitor.scope.context)
			out._new_from_long(ctx, c.ID(self.name))
			return out


	def not_(self, ctx):
		out = CIntegerLL(None, self.visitor)
		out.declare(self.visitor.scope.context)
		ctx.add(c.Assignment('=', c.ID(out.name), c.UnaryOp('!', c.ID(self.name))))
		return out


	def is_true(self, ctx, out_inst=None):
		if out_inst:
			ctx.add(c.Assignment('=', c.ID(out_inst.name), c.ID(self.name)))
		return self


	def set_constant(self, ctx, i):
		ctx.add(c.Assignment('=', c.ID(self.name), c.Constant('integer', i)))

from melano.c.types.pybool import PyBoolLL
from melano.c.types.pyinteger import PyIntegerLL

