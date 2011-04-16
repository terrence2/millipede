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


	def del_item_string(self, ctx, name:str):
		tmp = CIntegerLL(None, self.visitor)
		tmp.declare(self.visitor.scope.context, name='_del_rv')
		ctx.add(c.Assignment('=', c.ID(tmp.name), c.FuncCall(c.ID('PyDict_DelItemString'), c.ExprList(c.ID(self.name), c.Constant('string', name)))))
		self.fail_if_nonzero(ctx, tmp.name)


	def set_item_string(self, ctx, name:str, var:PyObjectLL):
		tmp = CIntegerLL(None, self.visitor)
		tmp.declare(self.visitor.scope.context, name='_set_rv')
		var = var.as_pyobject(ctx)
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


	def get_item_string(self, ctx, name:str, out:PyObjectLL, error_type='PyExc_KeyError', error_str=None):
		out.xdecref(ctx)
		ctx.add(c.Assignment('=', c.ID(out.name), c.FuncCall(c.ID('PyDict_GetItemString'), c.ExprList(
												c.ID(self.name), c.Constant('string', name)))))
		self.except_if_null(ctx, out.name, error_type, error_str)
		out.incref(ctx)
		return out


	def get_item_string_nofail(self, ctx, name:str, out:PyObjectLL):
		out.xdecref(ctx)
		ctx.add(c.Assignment('=', c.ID(out.name), c.FuncCall(c.ID('PyDict_GetItemString'), c.ExprList(
												c.ID(self.name), c.Constant('string', name)))))
		out.xincref(ctx)
		return out


	def update(self, ctx, other:PyObjectLL):
		tmp = CIntegerLL(None, self.visitor)
		tmp.declare(self.visitor.scope.context, name='_update_rv')
		ctx.add(c.Assignment('=', c.ID(tmp.name), c.FuncCall(c.ID('PyDict_Update'), c.ExprList(c.ID(self.name), c.ID(other.name)))))
		self.fail_if_nonzero(ctx, tmp.name)


	def copy(self, ctx, out_inst=None):
		if not out_inst:
			out_inst = PyDictLL(None, self.visitor)
			out_inst.declare(self.visitor.scope.context, name="_dict_cp")
		out_inst.xdecref(ctx)
		#FIXME: abort?!?
		ctx.add(c.If(c.UnaryOp('!', c.ID(self.name)), c.Compound(c.FuncCall(c.ID('abort'), c.ExprList())), None))
		ctx.add(c.Assignment('=', c.ID(out_inst.name), c.FuncCall(c.ID('PyDict_Copy'), c.ExprList(c.ID(self.name)))))
		self.fail_if_null(ctx, out_inst.name)
		return out_inst
