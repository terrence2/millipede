'''
Copyright (c) 2011, Terrence Cole.
All rights reserved.
'''
from melano.c import ast as c
from melano.c.types.pyobject import PyObjectType


class PyTupleType(PyObjectType):
	def pack(self, ctx, *to_pack):
		ids_to_pack = [c.ID(n) for n in to_pack] # turn the names into id's
		ctx.add(c.Assignment('=', c.ID(self.name), c.FuncCall(c.ID('PyTuple_Pack'), c.ExprList(
																							c.Constant('integer', len(ids_to_pack)), *ids_to_pack))))
		self.fail_if_null(ctx, self.name)
