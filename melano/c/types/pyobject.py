'''
Copyright (c) 2011, Terrence Cole.
All rights reserved.
'''
from melano.c import ast as c
from melano.c.types.lltype import LLType


class PyObjectLL(LLType):
	@staticmethod
	def typename():
		return 'PyObject'

	@staticmethod
	def typedecl(name=None):
		return c.PtrDecl(c.TypeDecl(name, c.IdentifierType('PyObject')))


	def declare(self, ctx, quals=[], name=None):
		super().declare(ctx, quals, name)
		ctx.add_variable(c.Decl(self.name, c.PtrDecl(c.TypeDecl(self.name, c.IdentifierType('PyObject'))), quals=quals, init=c.ID('NULL')), True)


	def clear(self, ctx):
		ctx.add(c.FuncCall(c.ID('Py_CLEAR'), c.ID(self.name)))


	def incref(self, ctx):
		ctx.add(c.FuncCall(c.ID('Py_INCREF'), c.ID(self.name)))


	def xincref(self, ctx):
		ctx.add(c.FuncCall(c.ID('Py_XINCREF'), c.ID(self.name)))


	def decref(self, ctx):
		ctx.add(c.FuncCall(c.ID('Py_DECREF'), c.ID(self.name)))


	def xdecref(self, ctx):
		ctx.add(c.FuncCall(c.ID('Py_XDECREF'), c.ID(self.name)))


	def as_pyobject(self, ctx):
		return self


	def str(self, ctx, out_inst=None):
		'''Convert to a string.'''
		if not out_inst:
			out_inst = PyObjectLL(None, self.visitor)
			out_inst.declare(self.visitor.scope.context, name="_str")
		ctx.add(c.Assignment('=', c.ID(out_inst.name), c.FuncCall(c.ID('PyObject_Str'), c.ExprList(c.ID(self.name)))))
		self.fail_if_null(ctx, out_inst.name)
		return out_inst


	def assign_none(self, ctx):
		ctx.add(c.Assignment('=', c.ID(self.name), c.ID(self.visitor.none.name)))


	def assign_name(self, ctx, from_var):
		ctx.add(c.Assignment('=', c.ID(self.name), c.ID(from_var.name)))
		ctx.add(c.FuncCall(c.ID('Py_INCREF'), c.ExprList(c.ID(self.name))))


	def get_length(self, ctx, out_inst=None):
		if not out_inst:
			out_inst = CIntegerLL(None, self.visitor)
			out_inst.declare(self.visitor.scope.context, name="_len")
		ctx.add(c.Assignment('=', c.ID(out_inst.name), c.FuncCall(c.ID('PyObject_Length'), c.ExprList(c.ID(self.name)))))
		self.fail_if_negative(ctx, out_inst.name)
		return out_inst


	def get_attr_string(self, ctx, attrname, out_var):
		ctx.add(c.Assignment('=', c.ID(out_var.name), c.FuncCall(c.ID('PyObject_GetAttrString'), c.ExprList(
														c.ID(self.name), c.Constant('string', attrname)))))
		self.fail_if_null(ctx, out_var.name)


	def set_attr_string(self, ctx, attrname, attrval):
		tmp = CIntegerLL(None, self.visitor)
		tmp.declare(self.visitor.scope.context, init= -1, name="setattr_rv")
		ctx.add(c.Assignment('=', c.ID(tmp.name), c.FuncCall(c.ID('PyObject_SetAttrString'), c.ExprList(
															c.ID(self.name), c.Constant('string', attrname), c.ID(attrval.name)))))
		self.fail_if_nonzero(ctx, tmp.name)


	def set_attr(self, ctx, attr, val):
		tmp = CIntegerLL(None, self.visitor)
		tmp.declare(self.visitor.scope.context, init= -1)
		ctx.add(c.Assignment('=', c.ID(tmp.name), c.FuncCall(c.ID('PyObject_SetAttr'), c.ExprList(
															c.ID(self.name), c.ID(attr.name), c.ID(val.name)))))
		self.fail_if_nonzero(ctx, tmp.name)


	def del_attr_string(self, ctx, attrname):
		tmp = CIntegerLL(None, self.visitor)
		tmp.declare(self.visitor.scope.context, init= -1)
		ctx.add(c.Assignment('=', c.ID(tmp.name), c.FuncCall(c.ID('PyObject_DelAttrString'), c.ExprList(
															c.ID(self.name), c.Constant('string', attrname)))))
		self.fail_if_nonzero(ctx, tmp.name)



	def get_item(self, ctx, key, out):
		ctx.add(c.Assignment('=', c.ID(out.name), c.FuncCall(c.ID('PyObject_GetItem'), c.ExprList(
															c.ID(self.name), c.ID(key.name)))))
		self.fail_if_null(ctx, out.name)


	def set_item(self, ctx, key, val):
		out = CIntegerLL(None, self.visitor)
		out.declare(self.visitor.scope.context, init= -1)
		ctx.add(c.Assignment('=', c.ID(out.name), c.FuncCall(c.ID('PyObject_SetItem'), c.ExprList(
															c.ID(self.name), c.ID(key.name), c.ID(val.name)))))
		self.fail_if_nonzero(ctx, out.name)
		return out


	def del_item(self, ctx, key):
		out = CIntegerLL(None, self.visitor)
		out.declare(self.visitor.scope.context, init= -1)
		ctx.add(c.Assignment('=', c.ID(out.name), c.FuncCall(c.ID('PyObject_DelItem'), c.ExprList(
															c.ID(self.name), c.ID(key.name)))))
		self.fail_if_nonzero(ctx, out.name)
		return out


	def call(self, ctx, posargs, kwargs, out_var):
		'''Returns the instance of the return value.'''
		posid = c.ID(posargs.name) if posargs else c.ID('NULL')
		kwid = c.ID(kwargs.name) if kwargs else c.ID('NULL')
		ctx.add(c.Assignment('=', c.ID(out_var.name), c.FuncCall(c.ID('PyObject_Call'), c.ExprList(c.ID(self.name), posid, kwid))))
		self.fail_if_null(ctx, out_var.name)


	## Binary Ops ##
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
		ctx.add(c.Assignment('=', c.ID(out.name), c.FuncCall(c.ID('PyNumber_Power'), c.ExprList(c.ID(self.name), c.ID(rhs.name), c.ID(self.visitor.none.name)))))
		self.fail_if_null(ctx, out.name)
	## END Binary Ops ##


	## Inplace Binary Ops ##
	def inplace_bitor(self, ctx, rhs, out):
		ctx.add(c.Assignment('=', c.ID(out.name), c.FuncCall(c.ID('PyNumber_InPlaceOr'), c.ExprList(c.ID(self.name), c.ID(rhs.name)))))
		self.fail_if_null(ctx, out.name)

	def inplace_bitxor(self, ctx, rhs, out):
		ctx.add(c.Assignment('=', c.ID(out.name), c.FuncCall(c.ID('PyNumber_InPlaceXor'), c.ExprList(c.ID(self.name), c.ID(rhs.name)))))
		self.fail_if_null(ctx, out.name)

	def inplace_bitand(self, ctx, rhs, out):
		ctx.add(c.Assignment('=', c.ID(out.name), c.FuncCall(c.ID('PyNumber_InPlaceAnd'), c.ExprList(c.ID(self.name), c.ID(rhs.name)))))
		self.fail_if_null(ctx, out.name)

	def inplace_lshift(self, ctx, rhs, out):
		ctx.add(c.Assignment('=', c.ID(out.name), c.FuncCall(c.ID('PyNumber_InPlaceLshift'), c.ExprList(c.ID(self.name), c.ID(rhs.name)))))
		self.fail_if_null(ctx, out.name)

	def inplace_rshift(self, ctx, rhs, out):
		ctx.add(c.Assignment('=', c.ID(out.name), c.FuncCall(c.ID('PyNumber_InPlaceRshift'), c.ExprList(c.ID(self.name), c.ID(rhs.name)))))
		self.fail_if_null(ctx, out.name)

	def inplace_add(self, ctx, rhs, out):
		ctx.add(c.Assignment('=', c.ID(out.name), c.FuncCall(c.ID('PyNumber_InPlaceAdd'), c.ExprList(c.ID(self.name), c.ID(rhs.name)))))
		self.fail_if_null(ctx, out.name)

	def inplace_subtract(self, ctx, rhs, out):
		ctx.add(c.Assignment('=', c.ID(out.name), c.FuncCall(c.ID('PyNumber_InPlaceSubtract'), c.ExprList(c.ID(self.name), c.ID(rhs.name)))))
		self.fail_if_null(ctx, out.name)

	def inplace_multiply(self, ctx, rhs, out):
		ctx.add(c.Assignment('=', c.ID(out.name), c.FuncCall(c.ID('PyNumber_InPlaceMultiply'), c.ExprList(c.ID(self.name), c.ID(rhs.name)))))
		self.fail_if_null(ctx, out.name)

	def inplace_divide(self, ctx, rhs, out):
		ctx.add(c.Assignment('=', c.ID(out.name), c.FuncCall(c.ID('PyNumber_InPlaceTrueDivide'), c.ExprList(c.ID(self.name), c.ID(rhs.name)))))
		self.fail_if_null(ctx, out.name)

	def inplace_floor_divide(self, ctx, rhs, out):
		ctx.add(c.Assignment('=', c.ID(out.name), c.FuncCall(c.ID('PyNumber_InPlaceFloorDivide'), c.ExprList(c.ID(self.name), c.ID(rhs.name)))))
		self.fail_if_null(ctx, out.name)

	def inplace_modulus(self, ctx, rhs, out):
		ctx.add(c.Assignment('=', c.ID(out.name), c.FuncCall(c.ID('PyNumber_InPlaceRemainder'), c.ExprList(c.ID(self.name), c.ID(rhs.name)))))
		self.fail_if_null(ctx, out.name)

	def inplace_power(self, ctx, rhs, out):
		ctx.add(c.Assignment('=', c.ID(out.name), c.FuncCall(c.ID('PyNumber_InPlacePower'), c.ExprList(c.ID(self.name), c.ID(rhs.name), c.ID(self.visitor.none.name)))))
		self.fail_if_null(ctx, out.name)
	## END Inplace Binary Ops ##


	## Unary Ops ##
	def invert(self, ctx, out):
		ctx.add(c.Assignment('=', c.ID(out.name), c.FuncCall(c.ID('PyNumber_Invert'), c.ExprList(c.ID(self.name)))))
		self.fail_if_null(ctx, out.name)


	def positive(self, ctx, out):
		ctx.add(c.Assignment('=', c.ID(out.name), c.FuncCall(c.ID('PyNumber_Positive'), c.ExprList(c.ID(self.name)))))
		self.fail_if_null(ctx, out.name)


	def negative(self, ctx, out):
		ctx.add(c.Assignment('=', c.ID(out.name), c.FuncCall(c.ID('PyNumber_Negative'), c.ExprList(c.ID(self.name)))))
		self.fail_if_null(ctx, out.name)


	def not_(self, ctx, out=None):
		if not out:
			out = CIntegerLL(None, self.visitor)
			out.declare(self.visitor.scope.context, name="_not_rv")
		ctx.add(c.Assignment('=', c.ID(out.name), c.FuncCall(c.ID('PyObject_Not'), c.ExprList(c.ID(self.name)))))
		self.fail_if_negative(ctx, out.name)
		return out
	## END Unary Ops ##


	def is_true(self, ctx, out_inst=None):
		if not out_inst:
			out_inst = CIntegerLL(None, self.visitor)
			out_inst.declare(self.visitor.scope.context)
		assert isinstance(out_inst, CIntegerLL)
		ctx.add(c.Assignment('=', c.ID(out_inst.name), c.FuncCall(c.ID('PyObject_IsTrue'), c.ExprList(c.ID(self.name)))))
		return out_inst


	def rich_compare_bool(self, ctx, rhs, opid):
		out = CIntegerLL(None, self.visitor)
		out.declare(self.visitor.scope.context)
		ctx.add(c.Assignment('=', c.ID(out.name), c.FuncCall(c.ID('PyObject_RichCompareBool'), c.ExprList(
																				c.ID(self.name), c.ID(rhs.name), c.ID(opid)))))
		self.fail_if_negative(ctx, out.name)
		return out


	### Sequence
	def sequence_contains(self, ctx, item):
		out = CIntegerLL(None, self.visitor)
		out.declare(self.visitor.scope.context)
		ctx.add(c.Assignment('=', c.ID(out.name), c.FuncCall(c.ID('PySequence_Contains'), c.ExprList(
																				c.ID(self.name), c.ID(item.name)))))
		self.fail_if_negative(ctx, out.name)
		return out


	def sequence_get_item(self, ctx, key, out):
		ctx.add(c.Assignment('=', c.ID(out.name), c.FuncCall(c.ID('PySequence_GetItem'), c.ExprList(
															c.ID(self.name), c.ID(key.name)))))
		self.fail_if_null(ctx, out.name)


	def sequence_inplace_concat(self, ctx, seq_inst, out_inst=None):
		if not out_inst:
			out_inst = PyObjectLL(None, self.visitor)
			out_inst.declare(self.visitor.scope.context)
		ctx.add(c.Assignment('=', c.ID(out_inst.name), c.FuncCall(c.ID('PySequence_InPlaceConcat'), c.ExprList(c.ID(self.name), c.ID(seq_inst.name)))))
		self.fail_if_null(ctx, out_inst.name)
		return out_inst


	def sequence_as_tuple(self, ctx, out_inst=None):
		if not out_inst:
			out_inst = PyTupleLL(None, self.visitor)
			out_inst.declare(self.visitor.scope.context)
		ctx.add(c.Assignment('=', c.ID(out_inst.name), c.FuncCall(c.ID('PySequence_Tuple'), c.ExprList(c.ID(self.name)))))
		return out_inst


	def sequence_get_slice(self, ctx,
						start:int or CIntegerLL,
						end:int or CIntegerLL,
						step:int or CIntegerLL,
						out=None):
		if not out:
			out = PyObjectLL(None, self.visitor)
			out.declare(self.visitor.scope.context)
		_start = c.Constant('integer', start) if isinstance(start, int) else c.ID(start.name)
		_end = c.Constant('integer', end) if isinstance(end, int) else c.ID(end.name)
		if step != 1:
			raise NotImplementedError("Slicing with a step size is not yet supported")
		ctx.add(c.Assignment('=', c.ID(out.name), c.FuncCall(c.ID('PySequence_GetSlice'), c.ExprList(c.ID(self.name), _start, _end))))
		self.fail_if_null(ctx, out.name)
		return out


	def sequence_del_slice(self, ctx,
						start:int or CIntegerLL,
						end:int or CIntegerLL,
						step:int or CIntegerLL):
		out = CIntegerLL(None, self.visitor)
		out.declare(self.visitor.scope.context)
		_start = c.Constant('integer', start) if isinstance(start, int) else c.ID(start.name)
		_end = c.Constant('integer', end) if isinstance(end, int) else c.ID(end.name)
		if step != 1:
			raise NotImplementedError("Slicing with a step size is not yet supported")
		ctx.add(c.Assignment('=', c.ID(out.name), c.FuncCall(c.ID('PySequence_DelSlice'), c.ExprList(c.ID(self.name), _start, _end))))
		self.fail_if_nonzero(ctx, out.name)
		return out
	### End Sequence


	def is_(self, ctx, other):
		out = CIntegerLL(None, self.visitor)
		out.declare(self.visitor.scope.context)
		ctx.add(c.Assignment('=', c.ID(out.name), c.BinaryOp('==', c.ID(self.name), c.ID(other.name))))
		return out


	def get_iter(self, ctx, iter):
		ctx.add(c.Assignment('=', c.ID(iter.name), c.FuncCall(c.ID('PyObject_GetIter'), c.ExprList(c.ID(self.name)))))
		self.fail_if_null(ctx, iter.name)


	def get_type(self, ctx, out):
		assert isinstance(out, PyTypeLL)
		ctx.add(c.Assignment('=', c.ID(out.name), c.FuncCall(c.ID('PyObject_Type'), c.ExprList(c.ID(self.name)))))
		self.fail_if_null(ctx, out.name)


	def as_ssize(self, ctx, out=None):
		if not out:
			out = CIntegerLL(None, self.visitor)
			out.declare(self.visitor.scope.context)
		assert isinstance(out, CIntegerLL)
		ctx.add(c.Assignment('=', c.ID(out.name), c.FuncCall(c.ID('PyNumber_AsSsize_t'), c.ExprList(c.ID(self.name), c.ID('PyExc_OverflowError')))))
		return out


	def is_instance(self, ctx, type_type):
		out = CIntegerLL(None, self.visitor)
		out.declare(self.visitor.scope.context)
		ctx.add(c.Assignment('=', c.ID(out.name), c.FuncCall(c.ID('PyObject_IsInstance'), c.ExprList(
									c.ID(self.name), c.Cast(PyObjectLL.typedecl(), c.UnaryOp('&', c.ID(type_type.typename())))))))
		self.fail_if_negative(ctx, out.name)
		return out


from melano.c.types.integer import CIntegerLL
from melano.c.types.pytuple import PyTupleLL
from melano.c.types.pytype import PyTypeLL
