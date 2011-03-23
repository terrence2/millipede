'''
Copyright (c) 2011, Terrence Cole.
All rights reserved.
'''
from melano.c import ast as c
from melano.c.types.integer import CIntegerLL
from melano.c.types.pyobject import PyObjectLL


class PyTupleLL(PyObjectLL):
	def new(self, ctx, size:int):
		ctx.add(c.Assignment('=', c.ID(self.name), c.FuncCall(c.ID('PyTuple_New'), c.ExprList(c.Constant('integer', size)))))
		self.fail_if_null(ctx, self.name)

	def set_item_unchecked(self, ctx, offset, var):
		ctx.add(c.FuncCall(c.ID('PyTuple_SET_ITEM'), c.ExprList(c.ID(self.name), c.Constant('integer', offset), c.ID(var.name))))


	def pack(self, ctx, *to_pack):
		ids_to_pack = []
		for inst in to_pack:
			if isinstance(inst, PyObjectLL):
				ids_to_pack.append(c.ID(inst.name))
			elif isinstance(inst, c.AST):
				ids_to_pack.append(inst)
			elif inst is None:
				ids_to_pack.append(c.ID('None'))
			else:
				raise ValueError('unrecognized type to pack in PyTupleLL.pack: {}'.format(inst))
		ctx.add(c.Assignment('=', c.ID(self.name), c.FuncCall(c.ID('PyTuple_Pack'), c.ExprList(
																						c.Constant('integer', len(ids_to_pack)), *ids_to_pack))))
		self.fail_if_null(ctx, self.name)


	def get_unchecked(self, ctx, offset, out_var):
		ctx.add(c.Assignment('=', c.ID(out_var.name), c.FuncCall(c.ID('PyTuple_GET_ITEM'), c.ExprList(c.ID(self.name), c.Constant('integer', offset)))))
		ctx.add(c.FuncCall(c.ID('Py_XINCREF'), c.ExprList(c.ID(out_var.name))))

	def get_size_unchecked(self, ctx, out_var):
		ctx.add(c.Assignment('=', c.ID(out_var.name), c.FuncCall(c.ID('PyTuple_GET_SIZE'), c.ExprList(c.ID(self.name)))))

	def get_var_unchecked(self, ctx, offset_var, out_var):
		ctx.add(c.Assignment('=', c.ID(out_var.name), c.FuncCall(c.ID('PyTuple_GET_ITEM'), c.ExprList(c.ID(self.name), c.ID(offset_var.name)))))
		ctx.add(c.FuncCall(c.ID('Py_XINCREF'), c.ExprList(c.ID(out_var.name))))

	def get_item(self, ctx, offset:CIntegerLL, out_var):
		ctx.add(c.Assignment('=', c.ID(out_var.name), c.FuncCall(c.ID('PyTuple_GetItem'), c.ExprList(c.ID(self.name), c.ID(offset.name)))))
		out_var.fail_if_null(ctx, out_var.name)
		out_var.incref(ctx)

