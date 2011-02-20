'''
Copyright (c) 2011, Terrence Cole.
All rights reserved.
'''
from melano.c import ast as c
from melano.c.types.integer import CIntegerType
from melano.c.types.lltype import LLType


class PyObjectType(LLType):
	def declare(self, ctx, quals=[]):
		ctx.add_variable(c.Decl(self.name, c.PtrDecl(c.TypeDecl(self.name, c.IdentifierType('PyObject'))), quals=quals, init=c.ID('NULL')), True)


	def delete(self, ctx):
		ctx.add(c.FuncCall(c.ID('Py_DECREF'), c.ID(self.name)))
		ctx.add(c.Assignment('=', c.ID(self.name), c.ID('NULL')))


	def incref(self, ctx):
		ctx.add(c.FuncCall(c.ID('Py_INCREF'), c.ID(self.name)))


	def as_pyobject(self, ctx):
		return self


	def assign_none(self, ctx):
		ctx.add(c.Assignment('=', c.ID(self.name), c.ID('None')))


	def assign_name(self, ctx, from_var):
		ctx.add(c.Assignment(' = ', c.ID(self.name), c.ID(from_var.name)))
		ctx.add(c.FuncCall(c.ID('Py_INCREF'), c.ExprList(c.ID(self.name))))


	def get_attr(self, ctx, attrname, out_varname):
		ctx.add(c.Assignment('=', c.ID(out_varname), c.FuncCall(c.ID('PyObject_GetAttrString'), c.ExprList(
														c.ID(self.name), c.Constant('string', attrname)))))
		self.fail_if_null(ctx, out_varname)


	def set_attr(self, ctx, attrname, attrval):
		tmp = ctx.tmpname()
		ctx.add_variable(c.Decl(tmp, c.TypeDecl(tmp, c.IdentifierType('int'))), False)
		ctx.add(c.Assignment('=', c.ID(tmp), c.FuncCall(c.ID('PyObject_SetAttrString'), c.ExprList(
															c.ID(self.name), c.Constant('string', attrname), c.ID(attrval.name)))))
		self.fail_if_nonzero(ctx, name=tmp)


	def call(self, ctx, posargs, kwargs, out_var):
		'''Returns the instance of the return value.'''
		posid = c.ID(posargs.name) if posargs else c.ID('NULL')
		kwid = c.ID(kwargs.name) if kwargs else c.ID('NULL')
		ctx.add(c.Assignment('=', c.ID(out_var.name), c.FuncCall(c.ID('PyObject_Call'), c.ExprList(c.ID(self.name), posid, kwid))))
		self.fail_if_null(ctx, out_var.name)


	def add(self, ctx, rhs, out):
		ctx.add(c.Assignment('=', c.ID(out.name), c.FuncCall(c.ID('PyNumber_Add'), c.ExprList(c.ID(self.name), c.ID(rhs.name)))))
		self.fail_if_null(ctx, out.name)


	def is_true(self, ctx):
		tmp = ctx.tmpname()
		ctx.add_variable(c.Decl(tmp, c.TypeDecl(tmp, c.IdentifierType('int'))), False)
		ctx.add(c.Assignment('=', c.ID(tmp), c.FuncCall(c.ID('PyObject_IsTrue'), c.ExprList(c.ID(self.name)))))
		return tmp


	def rich_compare_bool(self, ctx, rhs, opid):
		out = CIntegerType(ctx.tmpname())
		out.declare(ctx)
		ctx.add(c.Assignment('=', c.ID(out.name), c.FuncCall(c.ID('PyObject_RichCompareBool'), c.ExprList(
																				c.ID(self.name), c.ID(rhs.name), c.ID(opid)))))
		self.fail_if_negative(ctx, out.name)
		return out


	def sequence_contains(self, ctx, item):
		out = CIntegerType(ctx.tmpname())
		out.declare(ctx)
		ctx.add(c.Assignment('=', c.ID(out.name), c.FuncCall(c.ID('PySequence_Contains'), c.ExprList(
																				c.ID(self.name), c.ID(item.name)))))
		self.fail_if_negative(ctx, out.name)
		return out


	def is_(self, ctx, other):
		out = CIntegerType(ctx.tmpname())
		out.declare(ctx)
		ctx.add(c.Assignment('=', c.ID(out.name), c.BinaryOp('==', c.ID(self.name), c.ID(other.name))))
		return out

