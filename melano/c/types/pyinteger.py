'''
Copyright (c) 2011, Terrence Cole.
All rights reserved.
'''
from melano.c import ast as c
from melano.c.types.pyobject import PyObjectLL


class PyIntegerLL(PyObjectLL):
	def new(self, n):
		#FIXME: need a way to get the target architecture word size for this!
		if n < 2 ** 63 - 1:
			return self._new_from_long(c.Constant('integer', n))
		else:
			return self._new_from_string(c.Constant('string', str(n)))


	def set_constant(self, n):
		return self.new(n)


	def _new_from_long(self, c_n):
		self.xdecref()
		self.v.ctx.add(c.Assignment('=', c.ID(self.name), c.FuncCall(c.ID('PyLong_FromLong'), c.ExprList(c_n))))
		self.fail_if_null(self.name)


	def _new_from_string(self, c_s):
		self.xdecref()
		self.v.ctx.add(c.Assignment('=', c.ID(self.name), c.FuncCall(c.ID('PyLong_FromString'), c.ExprList(
																c_s, c.ID('NULL'), c.Constant('integer', 0)))))
		self.fail_if_null(self.name)
