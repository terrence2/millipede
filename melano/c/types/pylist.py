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


	def append(self, ctx, inst):
		tmp = CIntegerLL(None, self.visitor)
		tmp.declare(self.visitor.scope.context, name='_append_rv')
		ctx.add(c.Assignment('=', c.ID(tmp.name), c.FuncCall(c.ID('PyList_Append'), c.ExprList(c.ID(self.name), c.ID(inst.name)))))
		self.fail_if_nonzero(ctx, tmp.name)


	def pack(self, ctx, *to_pack):
		ids_to_pack = [c.ID(inst.name) if inst is not None else c.ID(self.visitor.none.name) for inst in to_pack]
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

