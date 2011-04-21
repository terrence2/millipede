'''
Copyright (c) 2011, Terrence Cole.
All rights reserved.
'''
from melano.c import ast as c
from melano.c.types.pyinteger import PyIntegerLL


class PyBoolLL(PyIntegerLL):
	def _new_from_long(self, c_ast):
		self.xdecref()
		self.v.ctx.add(c.Assignment('=', c.ID(self.name), c.FuncCall(c.ID('PyBool_FromLong'), c.ExprList(c_ast))))
		self.fail_if_null(self.name)
