'''
Copyright (c) 2011, Terrence Cole.
All rights reserved.
'''
from melano.c import ast as c
from melano.c.types.integer import CIntegerLL
from melano.c.types.pyobject import PyObjectLL


class PySetLL(PyObjectLL):
	def new(self, ctx, iterable=None):
		iterable_name = iterable.name if iterable else 'NULL'
		self.xdecref(ctx)
		ctx.add(c.Assignment('=', c.ID(self.name), c.FuncCall(c.ID('PySet_New'), c.ExprList(c.ID(iterable_name)))))
		self.fail_if_null(ctx, self.name)


	def add(self, ctx, val):
		out = CIntegerLL(None, self.visitor)
		out.declare(self.visitor.scope.context, name='_set_item_rv')
		ctx.add(c.Assignment('=', c.ID(out.name), c.FuncCall(c.ID('PySet_Add'), c.ExprList(
												c.ID(self.name), c.ID(val.name)))))
		self.fail_if_nonzero(ctx, out.name)


