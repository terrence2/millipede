'''
Copyright (c) 2011, Terrence Cole.
All rights reserved.
'''
from millipede.c import ast as c
from millipede.c.types.pyobject import PyObjectLL


class PyFloatLL(PyObjectLL):
	def new(self, n):
		super().new()
		return self._new_from_double(c.Constant('double', n))


	def _new_from_double(self, c_n):
		self.v.ctx.add(c.Assignment('=', c.ID(self.name), c.FuncCall(c.ID('PyFloat_FromDouble'), c.ExprList(c_n))))
		self.fail_if_null(self.name)


	def _new_from_string(self, c_s):
		self.v.ctx.add(c.Assignment('=', c.ID(self.name), c.FuncCall(c.ID('PyFloat_FromString'), c.ExprList(c_s))))
		self.fail_if_null(self.name)
