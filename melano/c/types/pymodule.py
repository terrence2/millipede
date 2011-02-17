'''
Copyright (c) 2011, Terrence Cole.
All rights reserved.
'''
from melano.c import ast as c
from melano.c.types.pyobject import PyObjectType


class PyModuleType(PyObjectType):
	#def declare(self, target):
	#	assert isinstance(target, c.TranslationUnit)
	#	target.add_variable(c.Decl(self.name, c.PtrDecl(c.TypeDecl(self.name, c.IdentifierType('PyObject'))), ['static']))

	def new(self, func, modname):
		func.add(c.Assignment('=', c.ID(self.name), c.FuncCall(c.ID('PyModule_New'), c.ExprList(c.Constant('string', modname)))))
		self.fail_if_null(self.name, func)
		func.cleanup.append(self.name)

	def get_dict(self, name, func):
		func.add(c.Assignment('=', c.ID(name), c.FuncCall(c.ID('PyModule_GetDict'), c.ExprList(c.ID(self.name)))))
		self.fail_if_null(self.name, func)

