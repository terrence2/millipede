'''
Copyright (c) 2011, Terrence Cole.
All rights reserved.
'''
from millipede.c import ast as c
from millipede.c.types.integer import CIntegerLL
from millipede.c.types.pyobject import PyObjectLL


class PyListLL(PyObjectLL):
	def new(self):
		super().new()
		self.v.ctx.add(c.Assignment('=', c.ID(self.name), c.FuncCall(c.ID('PyList_New'), c.ExprList(c.Constant('integer', 0)))))


	def append(self, inst, out_inst=None):
		if not out_inst:
			out_inst = CIntegerLL(None, self.v)
			out_inst.declare_tmp(name='_append_rv')
		self.v.ctx.add(c.Assignment('=', c.ID(out_inst.name), c.FuncCall(c.ID('PyList_Append'), c.ExprList(c.ID(self.name), c.ID(inst.name)))))
		self.fail_if_nonzero(out_inst.name)
		return out_inst


	def pack(self, *to_pack):
		ids_to_pack = []
		for inst in to_pack:
			if isinstance(inst, PyObjectLL):
				inst.incref()
				ids_to_pack.append(c.ID(inst.name))
			elif inst is None:
				self.v.none.incref()
				ids_to_pack.append(c.ID(self.v.none.name))
			else:
				raise ValueError('unrecognized type to pack in PyListLL.pack: {}'.format(inst))
		self.v.ctx.add(c.Assignment('=', c.ID(self.name), c.FuncCall(c.ID('PyList_New'), c.ExprList(c.Constant('integer', len(ids_to_pack))))))
		self.fail_if_null(self.name)
		for i, id in enumerate(ids_to_pack):
			self.v.ctx.add(c.FuncCall(c.ID('PyList_SET_ITEM'), c.ExprList(c.ID(self.name), c.Constant('integer', i), id)))


	def get_length(self, out_inst=None):
		if not out_inst:
			out_inst = CIntegerLL(None, self.v)
			out_inst.declare_tmp(name="_len")
		self.v.ctx.add(c.Assignment('=', c.ID(out_inst.name), c.FuncCall(c.ID('PyList_Size'), c.ExprList(c.ID(self.name)))))
		return out_inst

