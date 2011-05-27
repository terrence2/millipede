'''
Copyright (c) 2011, Terrence Cole.
All rights reserved.
'''
from millipede.c import ast as c
from millipede.c.types.pyinteger import PyIntegerLL
from millipede.c.types.pyobject import PyObjectLL


class PyBoolLL(PyIntegerLL):
	def _new_from_long(self, c_ast):
		PyObjectLL.new(self)
		self.v.ctx.add(c.Assignment('=', c.ID(self.name), c.FuncCall(c.ID('PyBool_FromLong'), c.ExprList(c_ast))))
		self.fail_if_null(self.name)
