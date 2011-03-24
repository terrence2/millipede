'''
Copyright (c) 2011, Terrence Cole.
All rights reserved.
'''
from melano.c import ast as c
from melano.c.types.pyobject import PyObjectLL


class PyListLL(PyObjectLL):
	def pack(self, ctx, *to_pack):
		ids_to_pack = [c.ID(inst.name) if inst is not None else c.ID(self.visitor.none.name) for inst in to_pack]
		ctx.add(c.Assignment('=', c.ID(self.name), c.FuncCall(c.ID('PyList_New'), c.ExprList(c.Constant('integer', len(ids_to_pack))))))
		self.fail_if_null(ctx, self.name)
		for i, id in enumerate(ids_to_pack):
			ctx.add(c.FuncCall(c.ID('PyList_SET_ITEM'), c.ExprList(c.ID(self.name), c.Constant('integer', i), id)))
