'''
Copyright (c) 2011, Terrence Cole.
All rights reserved.
'''
from melano.c import ast as c
from melano.c.types.pyobject import PyObjectType


class PyStringType(PyObjectType):
	ATTRS = {
				'strip': None
			}

	@classmethod
	def reference_attribute(cls, attr:str):
		return cls.ATTRS[attr]


	@classmethod
	def bytes2c(cls, b):
		'''Reformats a python bytes to make it suitable for use as a C string constant.'''
		s = str(b)[2:-1]
		return s.replace('"', '\\x22')


	@classmethod
	def str2c(cls, s):
		'''Reformats a python string to make it suitable for use as a C string constant.'''
		return s.replace('\n', '\\n').strip("'").strip('"')


	def new(self, ctx, init):
		# wchar_t is a signed type (!?!), so we need to do some checking here
		assert all(map(lambda x: ord(x) < 2 ** 31 and ord(x) >= 0, init)), 'Out of range character for wchar in: {}'.format(init)
		ctx.add(c.Assignment('=', c.ID(self.name), c.FuncCall(c.ID('PyUnicode_FromUnicode'), c.ExprList(
											c.Cast(c.PtrDecl(c.TypeDecl(self.name, c.IdentifierType('Py_UNICODE'))), c.Constant('string', init, prefix='L')),
											c.Constant('integer', len(init))))))
		self.fail_if_null(ctx, self.name)
