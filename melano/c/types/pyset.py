'''
Copyright (c) 2011, Terrence Cole.
All rights reserved.
'''
from melano.c import ast as c
from melano.c.types.pyobject import PyObjectLL


class PySetLL(PyObjectLL):
	def new(self, ctx, iterable):
		iterable_name = iterable.name if iterable else 'NULL'
		ctx.add(c.Assignment('=', c.ID(self.name), c.FuncCall(c.ID('PySet_New'), c.ExprList(c.ID(iterable_name)))))
		self.fail_if_null(ctx, self.name)


	def add(self, ctx, val):
		tmp = ctx.reserve_name('set_item_rv')
		ctx.add_variable(c.Decl(tmp, c.TypeDecl(tmp, c.IdentifierType('int'))), False)
		ctx.add(c.Assignment('=', c.ID(tmp), c.FuncCall(c.ID('PySet_Add'), c.ExprList(
												c.ID(self.name), c.ID(val.name)))))
		self.fail_if_nonzero(ctx, tmp)


