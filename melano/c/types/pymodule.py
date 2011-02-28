'''
Copyright (c) 2011, Terrence Cole.
All rights reserved.
'''
from melano.c import ast as c
from melano.c.types.pyobject import PyObjectLL


class PyModuleLL(PyObjectLL):

	def new(self, ctx, modname):
		ctx.add(c.Assignment('=', c.ID(self.name), c.FuncCall(c.ID('PyModule_New'), c.ExprList(c.Constant('string', modname)))))
		self.fail_if_null(ctx, self.name)

	def get_dict(self, ctx, out):
		ctx.add(c.Assignment('=', c.ID(out.name), c.FuncCall(c.ID('PyModule_GetDict'), c.ExprList(c.ID(self.name)))))
		self.fail_if_null(ctx, out.name)

