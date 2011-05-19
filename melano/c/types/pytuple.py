'''
Copyright (c) 2011, Terrence Cole.
All rights reserved.
'''
from melano.c import ast as c
from melano.c.types.integer import CIntegerLL
from melano.c.types.lltype import LLType
from melano.c.types.pyobject import PyObjectLL


class PyTupleLL(PyObjectLL):
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self._length = None


	def new(self, size:int or LLType):
		super().new()
		if isinstance(size, int):
			c_sz = c.Constant('integer', size)
			self._length = size
		elif isinstance(size, (CIntegerLL, PyObjectLL)):
			c_sz = c.ID(size.name)
		self.v.ctx.add(c.Assignment('=', c.ID(self.name), c.FuncCall(c.ID('PyTuple_New'), c.ExprList(c_sz))))
		self.fail_if_null(self.name)


	def set_item_unchecked(self, offset, var):
		self.v.ctx.add(c.FuncCall(c.ID('PyTuple_SET_ITEM'), c.ExprList(c.ID(self.name), c.Constant('integer', offset), c.ID(var.name))))


	def pack(self, *to_pack):
		ids_to_pack = []
		for inst in to_pack:
			if isinstance(inst, PyObjectLL):
				ids_to_pack.append(c.ID(inst.name))
			elif isinstance(inst, c.AST):
				ids_to_pack.append(inst)
			elif inst is None:
				ids_to_pack.append(c.ID(self.v.none.name))
			else:
				raise ValueError('unrecognized type to pack in PyTupleLL.pack: {}'.format(inst))
		self._length = len(ids_to_pack)
		self.v.ctx.add(c.Assignment('=', c.ID(self.name), c.FuncCall(c.ID('PyTuple_Pack'), c.ExprList(
																						c.Constant('integer', len(ids_to_pack)), *ids_to_pack))))
		self.fail_if_null(self.name)


	def get_unchecked(self, offset, out_var):
		self.v.ctx.add(c.Assignment('=', c.ID(out_var.name), c.FuncCall(c.ID('PyTuple_GET_ITEM'), c.ExprList(c.ID(self.name), c.Constant('integer', offset)))))
		self.v.ctx.add(c.FuncCall(c.ID('Py_XINCREF'), c.ExprList(c.ID(out_var.name))))


	def get_size_unchecked(self, out_var):
		self.v.ctx.add(c.Assignment('=', c.ID(out_var.name), c.FuncCall(c.ID('PyTuple_GET_SIZE'), c.ExprList(c.ID(self.name)))))


	def get_var_unchecked(self, offset_var, out_var):
		self.v.ctx.add(c.Assignment('=', c.ID(out_var.name), c.FuncCall(c.ID('PyTuple_GET_ITEM'), c.ExprList(c.ID(self.name), c.ID(offset_var.name)))))
		self.v.ctx.add(c.FuncCall(c.ID('Py_XINCREF'), c.ExprList(c.ID(out_var.name))))


	def get_item(self, offset:CIntegerLL, out_inst=None):
		if not isinstance(offset, CIntegerLL):
			offset = offset.as_ssize()
		if not out_inst:
			out_inst = PyObjectLL(None, self.v)
			out_inst.declare_tmp(name="_item")
		self.v.ctx.add(c.Assignment('=', c.ID(out_inst.name), c.FuncCall(c.ID('PyTuple_GetItem'), c.ExprList(c.ID(self.name), c.ID(offset.name)))))
		self.fail_if_null(out_inst.name)
		out_inst.incref()
		return out_inst


	def get_length(self, out_inst=None):
		if not out_inst:
			out_inst = CIntegerLL(None, self.v)
			out_inst.declare_tmp(name="_len")
		self.v.ctx.add(c.Assignment('=', c.ID(out_inst.name), c.FuncCall(c.ID('PyTuple_Size'), c.ExprList(c.ID(self.name)))))
		return out_inst


	def get_slice(self, start:int or CIntegerLL, end:int or CIntegerLL, out_inst=None):
		if not out_inst:
			out_inst = PyTupleLL(None, self.v)
			out_inst.declare_tmp(name="_slice_out")

		start_ref = c.Constant('integer', start) if isinstance(start, int) else c.ID(end.as_ssize().name)
		end_ref = c.Constant('integer', end) if isinstance(end, int) else c.ID(end.as_ssize().name)

		self.v.ctx.add(c.Assignment('=', c.ID(out_inst.name),
					c.FuncCall(c.ID('PyTuple_GetSlice'), c.ExprList(c.ID(self.name), start_ref, end_ref))))
		self.fail_if_null(out_inst.name)
		return out_inst

