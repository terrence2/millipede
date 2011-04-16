'''
Copyright (c) 2011, Terrence Cole.
All rights reserved.
'''
from melano.c import ast as c
from melano.c.types.integer import CIntegerLL
from melano.c.types.pyobject import PyObjectLL


class PyListLL(PyObjectLL):
	def new(self, ctx):
		self.xdecref(ctx)
		ctx.add(c.Assignment('=', c.ID(self.name), c.FuncCall(c.ID('PyList_New'), c.ExprList(c.Constant('integer', 0)))))


	def append(self, ctx, inst, out_inst=None):
		if not out_inst:
			out_inst = CIntegerLL(None, self.visitor)
			out_inst.declare(self.visitor.scope.context, name='_append_rv')
		ctx.add(c.Assignment('=', c.ID(out_inst.name), c.FuncCall(c.ID('PyList_Append'), c.ExprList(c.ID(self.name), c.ID(inst.name)))))
		self.fail_if_nonzero(ctx, out_inst.name)
		return out_inst


	def pack(self, ctx, *to_pack):
		ids_to_pack = []
		for inst in to_pack:
			if isinstance(inst, PyObjectLL):
				inst.incref(ctx)
				ids_to_pack.append(c.ID(inst.name))
			elif inst is None:
				self.visitor.none.incref(ctx)
				ids_to_pack.append(c.ID(self.visitor.none.name))
			else:
				raise ValueError('unrecognized type to pack in PyListLL.pack: {}'.format(inst))
		self.xdecref(ctx)
		ctx.add(c.Assignment('=', c.ID(self.name), c.FuncCall(c.ID('PyList_New'), c.ExprList(c.Constant('integer', len(ids_to_pack))))))
		self.fail_if_null(ctx, self.name)
		for i, id in enumerate(ids_to_pack):
			ctx.add(c.FuncCall(c.ID('PyList_SET_ITEM'), c.ExprList(c.ID(self.name), c.Constant('integer', i), id)))


	def get_length(self, ctx, out_inst=None):
		if not out_inst:
			out_inst = CIntegerLL(None, self.visitor)
			out_inst.declare(self.visitor.scope.context, name="_len")
		ctx.add(c.Assignment('=', c.ID(out_inst.name), c.FuncCall(c.ID('PyList_Size'), c.ExprList(c.ID(self.name)))))
		return out_inst

