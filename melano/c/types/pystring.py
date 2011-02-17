'''
Copyright (c) 2011, Terrence Cole.
All rights reserved.
'''
from melano.c import ast as c
from melano.c.types.pyobject import PyObjectType


class PyStringType(PyObjectType):

	def bytes2c(self, b):
		return str(b)[2:-1]

	#def declare(self, func):
	#	func.add_variable(c.Decl(self.name, c.PtrDecl(c.TypeDecl(self.name, c.IdentifierType('PyObject')))))

	def new(self, func, init):
		b = init.encode('UTF-32')
		s = self.bytes2c(b)
		func.add(c.Assignment('=', c.ID(self.name), c.FuncCall(c.ID('PyUnicode_FromUnicode'), c.ExprList(
											c.Cast(c.PtrDecl(c.TypeDecl(self.name, c.IdentifierType('Py_UNICODE'))), c.Constant('string', s)),
											c.Constant('integer', len(b))))))
		self.fail_if_null(self.name, func)
		func.cleanup.append(self.name)
