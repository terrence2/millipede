'''
Copyright (c) 2011, Terrence Cole.
All rights reserved.
'''
from melano.c import ast as c
from melano.c.types.pyobject import PyObjectLL


class PyDictType(PyObjectLL):
	def new(self, ctx):
		ctx.add(c.Assignment('=', c.ID(self.name), c.FuncCall(c.ID('PyDict_New'), c.ExprList())))
		self.fail_if_null(ctx, self.name)


	def set_item_string(self, ctx, name:str, var:PyObjectLL):
		tmp = ctx.reserve_name(self.name + '_set_item_rv', None, None)
		ctx.add_variable(c.Decl(tmp, c.TypeDecl(tmp, c.IdentifierType('int'))), False)
		ctx.add(c.Assignment('=', c.ID(tmp), c.FuncCall(c.ID('PyDict_SetItemString'), c.ExprList(
											c.ID(self.name), c.Constant('string', name), c.ID(var.name)))))
		self.fail_if_nonzero(ctx, tmp)


	def set_item(self, ctx, key:PyObjectLL, val:PyObjectLL):
		tmp = ctx.reserve_name(self.name + '_set_item_rv', None, None)
		ctx.add_variable(c.Decl(tmp, c.TypeDecl(tmp, c.IdentifierType('int'))), False)
		ctx.add(c.Assignment('=', c.ID(tmp), c.FuncCall(c.ID('PyDict_SetItem'), c.ExprList(
											c.ID(self.name), c.ID(key.name), c.ID(val.name)))))
		self.fail_if_nonzero(ctx, tmp)


	def get_item_string(self, ctx, name:str, out:PyObjectLL):
		ctx.add(c.Assignment('=', c.ID(out.name), c.FuncCall(c.ID('PyDict_GetItemString'), c.ExprList(
												c.ID(self.name), c.Constant('string', name)))))
		self.fail_if_null(ctx, out.name)
		ctx.add(c.FuncCall(c.ID('Py_INCREF'), c.ExprList(c.ID(out.name)))) # borrowed ref

