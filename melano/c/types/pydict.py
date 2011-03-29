'''
Copyright (c) 2011, Terrence Cole.
All rights reserved.
'''
from melano.c import ast as c
from melano.c.types.integer import CIntegerLL
from melano.c.types.pyobject import PyObjectLL


class PyDictLL(PyObjectLL):
	def new(self, ctx):
		ctx.add(c.Assignment('=', c.ID(self.name), c.FuncCall(c.ID('PyDict_New'), c.ExprList())))
		self.fail_if_null(ctx, self.name)


	def set_item_string(self, ctx, name:str, var:PyObjectLL):
		tmp = CIntegerLL(None, self.visitor)
		tmp.declare(self.visitor.scope.context, name='_set_rv')
		var.incref(ctx)
		ctx.add(c.Assignment('=', c.ID(tmp.name), c.FuncCall(c.ID('PyDict_SetItemString'), c.ExprList(
											c.ID(self.name), c.Constant('string', name), c.ID(var.name)))))
		self.fail_if_nonzero(ctx, tmp.name)


	def set_item(self, ctx, key:PyObjectLL, val:PyObjectLL):
		tmp = CIntegerLL(None, self.visitor)
		tmp.declare(self.visitor.scope.context, name='_set_rv')
		key.incref(ctx)
		val.incref(ctx)
		ctx.add(c.Assignment('=', c.ID(tmp.name), c.FuncCall(c.ID('PyDict_SetItem'), c.ExprList(
											c.ID(self.name), c.ID(key.name), c.ID(val.name)))))
		self.fail_if_nonzero(ctx, tmp.name)


	def get_item_string(self, ctx, name:str, out:PyObjectLL):
		ctx.add(c.Assignment('=', c.ID(out.name), c.FuncCall(c.ID('PyDict_GetItemString'), c.ExprList(
												c.ID(self.name), c.Constant('string', name)))))
		self.except_if_null(ctx, out.name, 'PyExc_KeyError')
		out.incref(ctx)


	def get_item_string_nofail(self, ctx, name:str, out:PyObjectLL):
		ctx.add(c.Assignment('=', c.ID(out.name), c.FuncCall(c.ID('PyDict_GetItemString'), c.ExprList(
												c.ID(self.name), c.Constant('string', name)))))
		out.xincref(ctx)


	def update(self, ctx, other:PyObjectLL):
		tmp = CIntegerLL(None, self.visitor)
		tmp.declare(self.visitor.scope.context, name='_update_rv')
		ctx.add(c.Assignment('=', c.ID(tmp.name), c.FuncCall(c.ID('PyDict_Update'), c.ExprList(c.ID(self.name), c.ID(other.name)))))
		self.fail_if_nonzero(ctx, tmp.name)

