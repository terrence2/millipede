'''
Copyright (c) 2011, Terrence Cole.
All rights reserved.
'''
from melano.c import ast as c
from melano.c.types.pyobject import PyObjectType


class PyTupleType(PyObjectType):
	def pack(self, func, *to_pack):
		to_pack = [c.ID(n) for n in to_pack] # turn the names into id's
		func.add(c.Assignment('=', c.ID(self.name), c.FuncCall(c.ID('PyTuple_Pack'), c.ExprList(
																							c.Constant('integer', len(to_pack)), *to_pack))))
		#NOTE: Pack increfs the args, so we only need to cleanup the tuple
		self.fail_if_null(self.name, func)
		func.cleanup.append(self.name)
