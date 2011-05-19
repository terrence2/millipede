'''
Copyright (c) 2011, Terrence Cole.
All rights reserved.
'''
from melano.c import ast as c
from melano.c.types.integer import CIntegerLL
from melano.c.types.pyobject import PyObjectLL


class PySetLL(PyObjectLL):
	def new(self, iterable=None):
		super().new()
		iterable_name = iterable.name if iterable else 'NULL'
		self.v.ctx.add(c.Assignment('=', c.ID(self.name), c.FuncCall(c.ID('PySet_New'), c.ExprList(c.ID(iterable_name)))))
		self.fail_if_null(self.name)


	def add(self, val):
		out = CIntegerLL(None, self.v)
		out.declare_tmp(name='_set_add_rv')
		self.v.ctx.add(c.Assignment('=', c.ID(out.name), c.FuncCall(c.ID('PySet_Add'), c.ExprList(
												c.ID(self.name), c.ID(val.name)))))
		self.fail_if_nonzero(out.name)
		out.decref()


