'''
Copyright (c) 2011, Terrence Cole.
All rights reserved.
'''
from melano.c import ast as c
from melano.c.types.pyobject import PyObjectLL


class PyIntegerLL(PyObjectLL):
	def new(self, ctx, n):
		#FIXME: need a way to get the target architecture word size for this!
		if n < 2 ** 63 - 1:
			return self._new_from_long(ctx, c.Constant('integer', n))
		else:
			return self._new_from_string(ctx, c.Constant('string', str(n)))


	def set_constant(self, ctx, n):
		return self.new(ctx, n)


	def _new_from_long(self, ctx, c_n):
		self.xdecref(ctx)
		ctx.add(c.Assignment('=', c.ID(self.name), c.FuncCall(c.ID('PyLong_FromLong'), c.ExprList(c_n))))
		self.fail_if_null(ctx, self.name)


	def _new_from_string(self, ctx, c_s):
		self.xdecref(ctx)
		ctx.add(c.Assignment('=', c.ID(self.name), c.FuncCall(c.ID('PyLong_FromString'), c.ExprList(
																c_s, c.ID('NULL'), c.Constant('integer', 0)))))
		self.fail_if_null(ctx, self.name)
