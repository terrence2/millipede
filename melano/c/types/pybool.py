'''
Copyright (c) 2011, Terrence Cole.
All rights reserved.
'''
from melano.c import ast as c
from melano.c.types.pyinteger import PyIntegerLL


class PyBoolLL(PyIntegerLL):
	def _new_from_long(self, ctx, c_ast):
		ctx.add(c.Assignment('=', c.ID(self.name), c.FuncCall(c.ID('PyBool_FromLong'), c.ExprList(c_ast))))
		self.fail_if_null(ctx, self.name)
