'''
Copyright (c) 2011, Terrence Cole.
All rights reserved.
'''
from melano.c import ast as c
from melano.c.types.integer import CIntegerLL
from melano.c.types.pyobject import PyObjectLL


class PySliceLL(PyObjectLL):
	def new(self, start, stop, step):
		super().new()
		self.xdecref()
		self.v.ctx.add(c.Assignment('=', c.ID(self.name), c.FuncCall(c.ID('PySlice_New'),
										c.ExprList(c.ID(start.name), c.ID(stop.name), c.ID(step.name))
										)))

