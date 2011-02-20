'''
Copyright (c) 2011, Terrence Cole.
All rights reserved.
'''
from melano.c import ast as c
from melano.c.types.pyobject import PyObjectType


class PyIntegerType(PyObjectType):
	def new(self, ctx, n):
		#FIXME: need a way to get the target architecture word size for this!
		if n < 2 ** 63 - 1:
			ctx.add(c.Assignment('=', c.ID(self.name), c.FuncCall(c.ID('PyLong_FromLong'), c.ExprList(c.Constant('integer', n)))))
		else:
			ctx.add(c.Assignment('=', c.ID(self.name), c.FuncCall(c.ID('PyLong_FromString'), c.ExprList(
																		c.Constant('string', str(n)), c.ID('NULL'), c.Constant('integer', 0)))))
		self.fail_if_null(ctx, self.name)
