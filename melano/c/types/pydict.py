'''
Copyright (c) 2011, Terrence Cole.
All rights reserved.
'''
from melano.c import ast as c
from melano.c.types.pyobject import PyObjectType


class PyDictType(PyObjectType):
	def new(self, func):
		func.add(c.Assignment('=', c.ID(self.name), c.FuncCall(c.ID('PyDict_New'), c.ExprList())))
		self.fail_if_null(self.name, func)
		func.cleanup.append(self.name)


	def set_item(self, func, name:str, varname:str):
		tmp = func.tmpname()
		func.add_variable(c.Decl(tmp, c.TypeDecl(tmp, c.IdentifierType('int'))))
		func.add(c.Assignment('=', c.ID(tmp), c.FuncCall(c.ID('PyDict_SetItemString'), c.ExprList(
											c.ID(self.name), c.Constant('string', name), c.ID(varname)))))
		self.fail_if_nonzero(tmp, func)


	def get_item(self, func, name:str, out_varname:str):
		#NOTE: this takes the out varname because the caller may know more about the expected type
		func.add(c.Assignment('=', c.ID(out_varname), c.FuncCall(c.ID('PyDict_GetItemString'), c.ExprList(
												c.ID(self.name), c.Constant('string', name)))))
		self.fail_if_null(out_varname, func)
		# borrowed ref
		func.add(c.FuncCall(c.ID('Py_INCREF'), c.ExprList(c.ID(out_varname))))
		func.cleanup.append(out_varname)

