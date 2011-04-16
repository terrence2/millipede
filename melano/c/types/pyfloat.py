'''
Copyright (c) 2011, Terrence Cole.
All rights reserved.
'''
from melano.c import ast as c
from melano.c.types.pyobject import PyObjectLL


class PyFloatLL(PyObjectLL):
	def new(self, ctx, n):
		return self._new_from_double(ctx, c.Constant('double', n))


	def _new_from_double(self, ctx, c_n):
		self.xdecref(ctx)
		ctx.add(c.Assignment('=', c.ID(self.name), c.FuncCall(c.ID('PyFloat_FromDouble'), c.ExprList(c_n))))
		self.fail_if_null(ctx, self.name)


	def _new_from_string(self, ctx, c_s):
		self.xdecref(ctx)
		ctx.add(c.Assignment('=', c.ID(self.name), c.FuncCall(c.ID('PyFloat_FromString'), c.ExprList(c_s))))
		self.fail_if_null(ctx, self.name)
