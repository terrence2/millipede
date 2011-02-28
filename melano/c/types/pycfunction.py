'''
Copyright (c) 2011, Terrence Cole.
All rights reserved.
'''
from melano.c import ast as c
from melano.c.types.pyobject import PyObjectLL


class PyCFunctionType(PyObjectLL):
	def new(self, ctx, funcdef_name, locals, modname):
		ctx.add(c.Assignment('=', c.ID(self.name), c.FuncCall(c.ID('PyCFunction_NewEx'), c.ExprList(
													c.UnaryOp('&', c.ID(funcdef_name)), c.ID(locals.name), c.ID(modname)))))
		self.fail_if_null(ctx, self.name)
