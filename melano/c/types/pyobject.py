'''
Copyright (c) 2011, Terrence Cole.
All rights reserved.
'''
from melano.c import ast as c
from melano.c.types.lltype import LLType


class PyObjectType(LLType):
	def declare(self, func, quals=[]):
		func.add_variable(c.Decl(self.name, c.PtrDecl(c.TypeDecl(self.name, c.IdentifierType('PyObject'))), init=c.ID('NULL')))


	def delete(self, func):
		func.add(c.FuncCall(c.ID('Py_DECREF'), c.ID(self.name)))
		func.cleanup.remove(self.name)


	def assign_none(self, func):
		func.add(c.Assignment('=', c.ID(self.name), c.ID('None')))


	def assign_name(self, func, varname):
		func.add(c.Assignment(' = ', c.ID(self.name), c.ID(varname)))
		func.add(c.FuncCall(c.ID('Py_INCREF'), c.ExprList(c.ID(self.name))))
		func.cleanup.append(self.name)


	def get_attr(self, func, attrname, out_varname):
		func.add(c.Assignment('=', c.ID(out_varname), c.FuncCall(c.ID('PyObject_GetAttrString'), c.ExprList(
														c.ID(self.name), c.Constant('string', attrname)))))
		self.fail_if_null(out_varname, func)
		func.cleanup.append(out_varname) # new ref


	def set_attr(self, func, attrname, attrval_varname):
		tmp = func.tmpname()
		func.add_variable(c.Decl(tmp, c.TypeDecl(tmp, c.IdentifierType('int'))))
		func.add(c.Assignment('=', c.ID(tmp), c.FuncCall(c.ID('PyObject_SetAttrString'), c.ExprList(
															c.ID(self.name), c.Constant('string', attrname), c.ID(attrval_varname)))))
		self.fail_if_nonzero(tmp, func)


	def call(self, func, posargs, kwargs):
		'''Returns the instance of the return value.'''
		rv = PyObjectType(func.tmpname())
		rv.declare(func)

		posid = c.ID(posargs.name) if posargs else c.ID('NULL')
		kwid = c.ID(kwargs.name) if kwargs else c.ID('NULL')
		func.add(c.Assignment('=', c.ID(rv.name), c.FuncCall(c.ID('PyObject_Call'), c.ExprList(c.ID(self.name), posid, kwid))))
		self.fail_if_null(rv.name, func)
		func.cleanup.append(rv.name)

		return rv


	def add(self, func, rhs_varname, out_varname):
		func.add(c.Assignment('=', c.ID(out_varname), c.FuncCall(c.ID('PyNumber_Add'), c.ExprList(c.ID(self.name), c.ID(rhs_varname)))))
		self.fail_if_null(out_varname, func)
		func.cleanup.append(out_varname)


	def is_true(self, func):
		tmp = func.tmpname()
		func.add_variable(c.Decl(tmp, c.TypeDecl(tmp, c.IdentifierType('int'))))
		func.add(c.Assignment('=', c.ID(tmp), c.FuncCall(c.ID('PyObject_IsTrue'), c.ExprList(c.ID(self.name)))))
		return tmp

