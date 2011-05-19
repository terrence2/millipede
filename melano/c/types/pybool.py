'''
Copyright (c) 2011, Terrence Cole.
All rights reserved.
'''
from melano.c import ast as c
from melano.c.types.pyinteger import PyIntegerLL
from melano.c.types.pyobject import PyObjectLL


class PyBoolLL(PyIntegerLL):
	def _new_from_long(self, c_ast):
		PyObjectLL.new(self)
		self.v.ctx.add(c.Assignment('=', c.ID(self.name), c.FuncCall(c.ID('PyBool_FromLong'), c.ExprList(c_ast))))
		self.fail_if_null(self.name)
