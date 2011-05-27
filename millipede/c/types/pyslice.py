'''
Copyright (c) 2011, Terrence Cole.
All rights reserved.
'''
from millipede.c import ast as c
from millipede.c.types.integer import CIntegerLL
from millipede.c.types.pyobject import PyObjectLL


class PySliceLL(PyObjectLL):
	def new(self, start, stop, step):
		super().new()
		self.v.ctx.add(c.Assignment('=', c.ID(self.name), c.FuncCall(c.ID('PySlice_New'),
										c.ExprList(c.ID(start.name), c.ID(stop.name), c.ID(step.name))
										)))

