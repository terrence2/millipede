'''
Copyright (c) 2011, Terrence Cole.
All rights reserved.
'''
from millipede.c import ast as c
from millipede.c.types.integer import CIntegerLL
from millipede.c.types.pyobject import PyObjectLL


class PyDictLL(PyObjectLL):
	def new(self):
		super().new()
		self.v.ctx.add(c.Assignment('=', c.ID(self.name), c.FuncCall(c.ID('PyDict_New'), c.ExprList())))
		self.fail_if_null(self.name)


	def del_item_string(self, name:str):
		tmp = CIntegerLL(None, self.v)
		tmp.declare_tmp(name='_del_rv')
		self.v.ctx.add(c.Assignment('=', c.ID(tmp.name), c.FuncCall(c.ID('PyDict_DelItemString'), c.ExprList(c.ID(self.name), c.Constant('string', name)))))
		self.fail_if_nonzero(tmp.name)


	def set_item_string(self, name:str, var:PyObjectLL):
		tmp = CIntegerLL(None, self.v)
		tmp.declare_tmp(name='_set_str_rv')
		var = var.as_pyobject()
		#var.incref()
		self.v.ctx.add(c.Assignment('=', c.ID(tmp.name), c.FuncCall(c.ID('PyDict_SetItemString'), c.ExprList(
											c.ID(self.name), c.Constant('string', name), c.ID(var.name)))))
		self.fail_if_nonzero(tmp.name)
		tmp.decref()


	def set_item(self, key:PyObjectLL, val:PyObjectLL):
		tmp = CIntegerLL(None, self.v)
		tmp.declare_tmp(name='_set_rv')
		#key.incref()
		#val.incref()
		self.v.ctx.add(c.Assignment('=', c.ID(tmp.name), c.FuncCall(c.ID('PyDict_SetItem'), c.ExprList(
											c.ID(self.name), c.ID(key.name), c.ID(val.name)))))
		self.fail_if_nonzero(tmp.name)
		tmp.decref()


	def get_item_string(self, name:str, out:PyObjectLL, error_type='PyExc_KeyError', error_str=None):
		self.v.ctx.add(c.Assignment('=', c.ID(out.name), c.FuncCall(c.ID('PyDict_GetItemString'), c.ExprList(
												c.ID(self.name), c.Constant('string', name)))))
		self.except_if_null(out.name, error_type, error_str)
		out.incref()
		return out


	def get_item_string_nofail(self, name:str, out:PyObjectLL):
		self.v.ctx.add(c.Assignment('=', c.ID(out.name), c.FuncCall(c.ID('PyDict_GetItemString'), c.ExprList(
												c.ID(self.name), c.Constant('string', name)))))
		out.xincref()
		return out


	def update(self, other:PyObjectLL):
		tmp = CIntegerLL(None, self.v)
		tmp.declare_tmp(name='_update_rv')
		self.v.ctx.add(c.Assignment('=', c.ID(tmp.name), c.FuncCall(c.ID('PyDict_Update'), c.ExprList(c.ID(self.name), c.ID(other.name)))))
		self.fail_if_nonzero(tmp.name)
		tmp.decref()


	def copy(self, out_inst=None):
		if not out_inst:
			out_inst = PyDictLL(None, self.v)
			out_inst.declare_tmp(name="_dict_cp")
		#FIXME: abort?!?
		self.v.ctx.add(c.If(c.UnaryOp('!', c.ID(self.name)), c.Compound(c.FuncCall(c.ID('abort'), c.ExprList())), None))
		self.v.ctx.add(c.Assignment('=', c.ID(out_inst.name), c.FuncCall(c.ID('PyDict_Copy'), c.ExprList(c.ID(self.name)))))
		self.fail_if_null(out_inst.name)
		return out_inst

