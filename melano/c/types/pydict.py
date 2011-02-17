'''
Copyright (c) 2011, Terrence Cole.
All rights reserved.
'''
from melano.c import ast as c
from melano.c.types.pyobject import PyObjectType


class PyDictType(PyObjectType):
	#def declare(self, target):
	#	quals = []
	#	if isinstance(target, c.TranslationUnit):
	#		quals.append('static')
	#	target.add_variable(c.Decl(self.name, c.PtrDecl(c.TypeDecl(self.name, c.IdentifierType('PyObject'))), quals))

	def set_item(self, func, name:str, varname:str):
		tmp = func.tmpname()
		func.add(c.Assignment('=', c.ID(tmp), c.FuncCall(c.ID('PyDict_SetItemString'), c.ExprList(
											c.ID(self.name), c.Constant('string', name), c.ID(varname)))))
		self.fail_if_nonzero(tmp, func)
