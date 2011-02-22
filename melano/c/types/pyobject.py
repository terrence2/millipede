'''
Copyright (c) 2011, Terrence Cole.
All rights reserved.
'''
from melano.c import ast as c
from melano.c.types.lltype import LLType


class PyObjectType(LLType):
	def declare(self, ctx, quals=[]):
		assert isinstance(ctx, c.TranslationUnit) or not ctx._visitor.scopes or ctx._visitor.scope.context == ctx
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


	def get_attr_string(self, ctx, attrname, out_var):
		ctx.add(c.Assignment('=', c.ID(out_var.name), c.FuncCall(c.ID('PyObject_GetAttrString'), c.ExprList(
														c.ID(self.name), c.Constant('string', attrname)))))
		self.fail_if_null(ctx, out_var.name)


	def set_attr_string(self, ctx, attrname, attrval):
		tmp = CIntegerType(ctx.tmpname())
		tmp.declare(ctx, init= -1)
		ctx.add(c.Assignment('=', c.ID(tmp.name), c.FuncCall(c.ID('PyObject_SetAttrString'), c.ExprList(
															c.ID(self.name), c.Constant('string', attrname), c.ID(attrval.name)))))
		self.fail_if_nonzero(ctx, tmp.name)
		return tmp


	def get_item(self, ctx, key, out):
		ctx.add(c.Assignment('=', c.ID(out.name), c.FuncCall(c.ID('PyObject_GetItem'), c.ExprList(
															c.ID(self.name), c.ID(key.name)))))
		self.fail_if_null(ctx, out.name)


	def set_item(self, ctx, key, val):
		tmp = CIntegerType(ctx.tmpname())
		tmp.declare(ctx, init= -1)
		ctx.add(c.Assignment('=', c.ID(tmp.name), c.FuncCall(c.ID('PyObject_SetItem'), c.ExprList(
															c.ID(self.name), c.ID(key.name), c.ID(val.name)))))
		self.fail_if_nonzero(ctx, tmp.name)
		return tmp


	def call(self, ctx, posargs, kwargs, out_var):
		'''Returns the instance of the return value.'''
		posid = c.ID(posargs.name) if posargs else c.ID('NULL')
		kwid = c.ID(kwargs.name) if kwargs else c.ID('NULL')
		ctx.add(c.Assignment('=', c.ID(out_var.name), c.FuncCall(c.ID('PyObject_Call'), c.ExprList(c.ID(self.name), posid, kwid))))
		self.fail_if_null(ctx, out_var.name)



	def bitor(self, ctx, rhs, out):
		ctx.add(c.Assignment('=', c.ID(out.name), c.FuncCall(c.ID('PyNumber_Or'), c.ExprList(c.ID(self.name), c.ID(rhs.name)))))
		self.fail_if_null(ctx, out.name)


	def bitxor(self, ctx, rhs, out):
		ctx.add(c.Assignment('=', c.ID(out.name), c.FuncCall(c.ID('PyNumber_Xor'), c.ExprList(c.ID(self.name), c.ID(rhs.name)))))
		self.fail_if_null(ctx, out.name)


	def bitand(self, ctx, rhs, out):
		ctx.add(c.Assignment('=', c.ID(out.name), c.FuncCall(c.ID('PyNumber_And'), c.ExprList(c.ID(self.name), c.ID(rhs.name)))))
		self.fail_if_null(ctx, out.name)


	def lshift(self, ctx, rhs, out):
		ctx.add(c.Assignment('=', c.ID(out.name), c.FuncCall(c.ID('PyNumber_Lshift'), c.ExprList(c.ID(self.name), c.ID(rhs.name)))))
		self.fail_if_null(ctx, out.name)


	def rshift(self, ctx, rhs, out):
		ctx.add(c.Assignment('=', c.ID(out.name), c.FuncCall(c.ID('PyNumber_Rshift'), c.ExprList(c.ID(self.name), c.ID(rhs.name)))))
		self.fail_if_null(ctx, out.name)


	def add(self, ctx, rhs, out):
		ctx.add(c.Assignment('=', c.ID(out.name), c.FuncCall(c.ID('PyNumber_Add'), c.ExprList(c.ID(self.name), c.ID(rhs.name)))))
		self.fail_if_null(ctx, out.name)


	def subtract(self, ctx, rhs, out):
		ctx.add(c.Assignment('=', c.ID(out.name), c.FuncCall(c.ID('PyNumber_Subtract'), c.ExprList(c.ID(self.name), c.ID(rhs.name)))))
		self.fail_if_null(ctx, out.name)


	def multiply(self, ctx, rhs, out):
		ctx.add(c.Assignment('=', c.ID(out.name), c.FuncCall(c.ID('PyNumber_Multiply'), c.ExprList(c.ID(self.name), c.ID(rhs.name)))))
		self.fail_if_null(ctx, out.name)


	def divide(self, ctx, rhs, out):
		ctx.add(c.Assignment('=', c.ID(out.name), c.FuncCall(c.ID('PyNumber_TrueDivide'), c.ExprList(c.ID(self.name), c.ID(rhs.name)))))
		self.fail_if_null(ctx, out.name)


	def floor_divide(self, ctx, rhs, out):
		ctx.add(c.Assignment('=', c.ID(out.name), c.FuncCall(c.ID('PyNumber_FloorDivide'), c.ExprList(c.ID(self.name), c.ID(rhs.name)))))
		self.fail_if_null(ctx, out.name)


	def modulus(self, ctx, rhs, out):
		ctx.add(c.Assignment('=', c.ID(out.name), c.FuncCall(c.ID('PyNumber_Remainder'), c.ExprList(c.ID(self.name), c.ID(rhs.name)))))
		self.fail_if_null(ctx, out.name)


	def power(self, ctx, rhs, out):
		ctx.add(c.Assignment('=', c.ID(out.name), c.FuncCall(c.ID('PyNumber_Power'), c.ExprList(c.ID(self.name), c.ID(rhs.name), c.ID('None')))))
		self.fail_if_null(ctx, out.name)


	def invert(self, ctx, out):
		ctx.add(c.Assignment('=', c.ID(out.name), c.FuncCall(c.ID('PyNumber_Invert'), c.ExprList(c.ID(self.name)))))
		self.fail_if_null(ctx, out.name)


	def positive(self, ctx, out):
		ctx.add(c.Assignment('=', c.ID(out.name), c.FuncCall(c.ID('PyNumber_Positive'), c.ExprList(c.ID(self.name)))))
		self.fail_if_null(ctx, out.name)


	def negative(self, ctx, out):
		ctx.add(c.Assignment('=', c.ID(out.name), c.FuncCall(c.ID('PyNumber_Negative'), c.ExprList(c.ID(self.name)))))
		self.fail_if_null(ctx, out.name)


	def not_(self, ctx, out):
		ctx.add(c.Assignment('=', c.ID(out.name), c.FuncCall(c.ID('PyObject_Not'), c.ExprList(c.ID(self.name)))))
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


	def get_iter(self, ctx):
		out = PyObjectType(ctx.tmpname())
		out.declare(ctx)
		ctx.add(c.Assignment('=', c.ID(out.name), c.FuncCall(c.ID('PyObject_GetIter'), c.ExprList(c.ID(self.name)))))
		self.fail_if_null(ctx, out.name)
		return out


	def get_type(self, ctx):
		out = PyTypeType(ctx.tmpname())
		out.declare(ctx)
		ctx.add(c.Assignment('=', c.ID(out.name), c.FuncCall(c.ID('PyObject_Type'), c.ExprList(c.ID(self.name)))))
		self.fail_if_null(ctx, out.name)
		return out


	def is_instance(self, ctx, type_id):
		out = CIntegerType(ctx.tmpname())
		out.declare(ctx)
		ctx.add(c.Assignment('=', c.ID(out.name), c.FuncCall(c.ID('PyObject_IsInstance'), c.ExprList(
																				c.ID(self.name), type_id))))
		self.fail_if_negative(ctx, out.name)
		return out


from melano.c.types.pytype import PyTypeType
from melano.c.types.integer import CIntegerType
