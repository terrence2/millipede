'''
Copyright (c) 2011, Terrence Cole.
All rights reserved.
'''
from melano.c import ast as c
from melano.c.types.pyobject import PyObjectLL
from melano.c.types.pystring import PyStringLL


class PyBytesLL(PyObjectLL):
	@classmethod
	def bytes2c(cls, b):
		'''Reformats a python bytes to make it suitable for use as a C string constant.'''
		# FIXME: make this work
		return b


	@classmethod
	def strlen(cls, b):
		return len(b)


	def new(self, py_init):
		super().new()
		init = self.bytes2c(py_init)
		strlen = self.strlen(init)
		assert all(map(lambda x: ord(x) < 256 and ord(x) >= 0, init)), 'Out of range character for char in: {}'.format(init)
		self.v.ctx.add(c.Assignment('=', c.ID(self.name), c.FuncCall(c.ID('PyBytes_FromStringAndSize'), c.ExprList(
											c.Constant('string', init),
											c.Constant('integer', strlen)))))
		self.fail_if_null(self.name)


