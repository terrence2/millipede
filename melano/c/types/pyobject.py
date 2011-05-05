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


	def declare(self, *, is_global=False, quals=[], name=None, need_cleanup=True, **kwargs):
		super().declare(is_global=is_global, quals=quals, name=name, **kwargs)
		ctx = self.v.tu if is_global else self.v.scope.ctx
		ctx.add_variable(c.Decl(self.name, self.typedecl(self.name), quals=quals, init=c.ID('NULL')), need_cleanup=need_cleanup)


	def clear(self):
		self.v.ctx.add(c.FuncCall(c.ID('Py_CLEAR'), c.ID(self.name)))


	def incref(self):
		self.v.ctx.add(c.FuncCall(c.ID('Py_INCREF'), c.ID(self.name)))


	def xincref(self):
		self.v.ctx.add(c.FuncCall(c.ID('Py_XINCREF'), c.ID(self.name)))


	def decref(self):
		self.v.ctx.add(c.FuncCall(c.ID('Py_DECREF'), c.ID(self.name)))


	def xdecref(self):
		self.v.ctx.add(c.FuncCall(c.ID('Py_XDECREF'), c.ID(self.name)))


	def as_pyobject(self):
		return self


	def str(self, out_inst=None):
		'''Convert to a string.'''
		if not out_inst:
			out_inst = PyStringLL(None, self.v)
			out_inst.declare(name="_str")
		out_inst.xdecref()
		self.v.ctx.add(c.Assignment('=', c.ID(out_inst.name), c.FuncCall(c.ID('PyObject_Str'), c.ExprList(c.ID(self.name)))))
		self.fail_if_null(out_inst.name)
		return out_inst


	def assign_none(self):
		self.xdecref()
		self.v.none.incref()
		self.v.ctx.add(c.Assignment('=', c.ID(self.name), c.ID(self.v.none.name)))


	def assign_name(self, from_var):
		self.xdecref()
		from_var = from_var.as_pyobject()
		from_var.xincref()
		self.v.ctx.add(c.Assignment('=', c.ID(self.name), c.ID(from_var.name)))


	def get_length(self, out_inst=None):
		if not out_inst:
			out_inst = CIntegerLL(None, self.v)
			out_inst.declare(name="_len")
		self.v.ctx.add(c.Assignment('=', c.ID(out_inst.name), c.FuncCall(c.ID('PyObject_Length'), c.ExprList(c.ID(self.name)))))
		self.fail_if_negative(out_inst.name)
		return out_inst


	def get_attr_string(self, attrname, out_var):
		out_var.xdecref()
		self.v.ctx.add(c.Assignment('=', c.ID(out_var.name), c.FuncCall(c.ID('PyObject_GetAttrString'), c.ExprList(
														c.ID(self.name), c.Constant('string', attrname)))))
		self.fail_if_null(out_var.name)


	def get_attr_string_with_exception(self, attrname, out_var, exc_name, exc_str=None):
		out_var.xdecref()
		self.v.ctx.add(c.Assignment('=', c.ID(out_var.name), c.FuncCall(c.ID('PyObject_GetAttrString'), c.ExprList(
														c.ID(self.name), c.Constant('string', attrname)))))
		failed = self.v.ctx.add(c.If(c.UnaryOp('!', c.ID(out_var.name)), c.Compound(), None))
		with self.v.new_context(failed.iftrue):
			self.v.ctx.add(c.FuncCall(c.ID('PyErr_Clear'), c.ExprList()))
			if exc_str:
				self.v.ctx.add(c.FuncCall(c.ID('PyErr_SetString'), c.ExprList(c.ID(exc_name), c.Constant('string', exc_str))))
			else:
				self.v.ctx.add(c.FuncCall(c.ID('PyErr_SetNone'), c.ExprList(c.ID(exc_name))))
			self.v.capture_error()
			self.v.exit_with_exception()


	def set_attr_string(self, attrname, attrval):
		tmp = CIntegerLL(None, self.v)
		tmp.declare(init= -1, name="setattr_rv")
		attrval = attrval.as_pyobject()
		self.v.ctx.add(c.Assignment('=', c.ID(tmp.name), c.FuncCall(c.ID('PyObject_SetAttrString'), c.ExprList(
															c.ID(self.name), c.Constant('string', attrname), c.ID(attrval.name)))))
		self.fail_if_nonzero(tmp.name)


	def set_attr(self, attr, val):
		tmp = CIntegerLL(None, self.v)
		tmp.declare(init= -1)
		self.v.ctx.add(c.Assignment('=', c.ID(tmp.name), c.FuncCall(c.ID('PyObject_SetAttr'), c.ExprList(
															c.ID(self.name), c.ID(attr.name), c.ID(val.name)))))
		self.fail_if_nonzero(tmp.name)


	def del_attr_string(self, attrname):
		tmp = CIntegerLL(None, self.v)
		tmp.declare(init= -1)
		self.v.ctx.add(c.Assignment('=', c.ID(tmp.name), c.FuncCall(c.ID('PyObject_DelAttrString'), c.ExprList(
															c.ID(self.name), c.Constant('string', attrname)))))
		self.fail_if_nonzero(tmp.name)



	def get_item(self, key, out_inst=None):
		if not out_inst:
			out_inst = PyObjectLL(None, self.v)
			out_inst.declare(name="_item")
		out_inst.xdecref()
		self.v.ctx.add(c.Assignment('=', c.ID(out_inst.name), c.FuncCall(c.ID('PyObject_GetItem'), c.ExprList(
															c.ID(self.name), c.ID(key.name)))))
		self.fail_if_null(out_inst.name)
		return out_inst


	def set_item(self, key, val):
		out = CIntegerLL(None, self.v)
		out.declare(init= -1)
		self.v.ctx.add(c.Assignment('=', c.ID(out.name), c.FuncCall(c.ID('PyObject_SetItem'), c.ExprList(
															c.ID(self.name), c.ID(key.name), c.ID(val.name)))))
		self.fail_if_nonzero(out.name)
		return out


	def del_item(self, key):
		out = CIntegerLL(None, self.v)
		out.declare(init= -1)
		self.v.ctx.add(c.Assignment('=', c.ID(out.name), c.FuncCall(c.ID('PyObject_DelItem'), c.ExprList(
															c.ID(self.name), c.ID(key.name)))))
		self.fail_if_nonzero(out.name)
		return out


	def call(self, posargs, kwargs, out_var):
		'''Returns the instance of the return value.'''
		posid = c.ID(posargs.name) if posargs else c.ID('NULL')
		kwid = c.ID(kwargs.name) if kwargs else c.ID('NULL')
		out_var.xdecref()
		self.v.ctx.add(c.Assignment('=', c.ID(out_var.name), c.FuncCall(c.ID('PyObject_Call'), c.ExprList(c.ID(self.name), posid, kwid))))
		self.fail_if_null(out_var.name)


	## Binary Ops ##
	def bitor(self, rhs, out):
		out.xdecref()
		self.v.ctx.add(c.Assignment('=', c.ID(out.name), c.FuncCall(c.ID('PyNumber_Or'), c.ExprList(c.ID(self.name), c.ID(rhs.name)))))
		self.fail_if_null(out.name)


	def bitxor(self, rhs, out):
		out.xdecref()
		self.v.ctx.add(c.Assignment('=', c.ID(out.name), c.FuncCall(c.ID('PyNumber_Xor'), c.ExprList(c.ID(self.name), c.ID(rhs.name)))))
		self.fail_if_null(out.name)


	def bitand(self, rhs, out):
		out.xdecref()
		self.v.ctx.add(c.Assignment('=', c.ID(out.name), c.FuncCall(c.ID('PyNumber_And'), c.ExprList(c.ID(self.name), c.ID(rhs.name)))))
		self.fail_if_null(out.name)


	def lshift(self, rhs, out):
		out.xdecref()
		self.v.ctx.add(c.Assignment('=', c.ID(out.name), c.FuncCall(c.ID('PyNumber_Lshift'), c.ExprList(c.ID(self.name), c.ID(rhs.name)))))
		self.fail_if_null(out.name)


	def rshift(self, rhs, out):
		out.xdecref()
		self.v.ctx.add(c.Assignment('=', c.ID(out.name), c.FuncCall(c.ID('PyNumber_Rshift'), c.ExprList(c.ID(self.name), c.ID(rhs.name)))))
		self.fail_if_null(out.name)


	def add(self, rhs, out):
		out.xdecref()
		self.v.ctx.add(c.Assignment('=', c.ID(out.name), c.FuncCall(c.ID('PyNumber_Add'), c.ExprList(c.ID(self.name), c.ID(rhs.name)))))
		self.fail_if_null(out.name)


	def subtract(self, rhs, out):
		out.xdecref()
		self.v.ctx.add(c.Assignment('=', c.ID(out.name), c.FuncCall(c.ID('PyNumber_Subtract'), c.ExprList(c.ID(self.name), c.ID(rhs.name)))))
		self.fail_if_null(out.name)


	def multiply(self, rhs, out):
		out.xdecref()
		self.v.ctx.add(c.Assignment('=', c.ID(out.name), c.FuncCall(c.ID('PyNumber_Multiply'), c.ExprList(c.ID(self.name), c.ID(rhs.name)))))
		self.fail_if_null(out.name)


	def divide(self, rhs, out):
		out.xdecref()
		self.v.ctx.add(c.Assignment('=', c.ID(out.name), c.FuncCall(c.ID('PyNumber_TrueDivide'), c.ExprList(c.ID(self.name), c.ID(rhs.name)))))
		self.fail_if_null(out.name)


	def floor_divide(self, rhs, out):
		out.xdecref()
		self.v.ctx.add(c.Assignment('=', c.ID(out.name), c.FuncCall(c.ID('PyNumber_FloorDivide'), c.ExprList(c.ID(self.name), c.ID(rhs.name)))))
		self.fail_if_null(out.name)


	def modulus(self, rhs, out):
		out.xdecref()
		self.v.ctx.add(c.Assignment('=', c.ID(out.name), c.FuncCall(c.ID('PyNumber_Remainder'), c.ExprList(c.ID(self.name), c.ID(rhs.name)))))
		self.fail_if_null(out.name)


	def power(self, rhs, out):
		out.xdecref()
		self.v.ctx.add(c.Assignment('=', c.ID(out.name), c.FuncCall(c.ID('PyNumber_Power'), c.ExprList(c.ID(self.name), c.ID(rhs.name), c.ID(self.v.none.name)))))
		self.fail_if_null(out.name)
	## END Binary Ops ##


	## Inplace Binary Ops ##
	def inplace_bitor(self, rhs, out):
		out.xdecref()
		self.v.ctx.add(c.Assignment('=', c.ID(out.name), c.FuncCall(c.ID('PyNumber_InPlaceOr'), c.ExprList(c.ID(self.name), c.ID(rhs.name)))))
		self.fail_if_null(out.name)

	def inplace_bitxor(self, rhs, out):
		out.xdecref()
		self.v.ctx.add(c.Assignment('=', c.ID(out.name), c.FuncCall(c.ID('PyNumber_InPlaceXor'), c.ExprList(c.ID(self.name), c.ID(rhs.name)))))
		self.fail_if_null(out.name)

	def inplace_bitand(self, rhs, out):
		out.xdecref()
		self.v.ctx.add(c.Assignment('=', c.ID(out.name), c.FuncCall(c.ID('PyNumber_InPlaceAnd'), c.ExprList(c.ID(self.name), c.ID(rhs.name)))))
		self.fail_if_null(out.name)

	def inplace_lshift(self, rhs, out):
		out.xdecref()
		self.v.ctx.add(c.Assignment('=', c.ID(out.name), c.FuncCall(c.ID('PyNumber_InPlaceLshift'), c.ExprList(c.ID(self.name), c.ID(rhs.name)))))
		self.fail_if_null(out.name)

	def inplace_rshift(self, rhs, out):
		out.xdecref()
		self.v.ctx.add(c.Assignment('=', c.ID(out.name), c.FuncCall(c.ID('PyNumber_InPlaceRshift'), c.ExprList(c.ID(self.name), c.ID(rhs.name)))))
		self.fail_if_null(out.name)

	def inplace_add(self, rhs, out):
		out.xdecref()
		self.v.ctx.add(c.Assignment('=', c.ID(out.name), c.FuncCall(c.ID('PyNumber_InPlaceAdd'), c.ExprList(c.ID(self.name), c.ID(rhs.name)))))
		self.fail_if_null(out.name)

	def inplace_subtract(self, rhs, out):
		out.xdecref()
		self.v.ctx.add(c.Assignment('=', c.ID(out.name), c.FuncCall(c.ID('PyNumber_InPlaceSubtract'), c.ExprList(c.ID(self.name), c.ID(rhs.name)))))
		self.fail_if_null(out.name)

	def inplace_multiply(self, rhs, out):
		out.xdecref()
		self.v.ctx.add(c.Assignment('=', c.ID(out.name), c.FuncCall(c.ID('PyNumber_InPlaceMultiply'), c.ExprList(c.ID(self.name), c.ID(rhs.name)))))
		self.fail_if_null(out.name)

	def inplace_divide(self, rhs, out):
		out.xdecref()
		self.v.ctx.add(c.Assignment('=', c.ID(out.name), c.FuncCall(c.ID('PyNumber_InPlaceTrueDivide'), c.ExprList(c.ID(self.name), c.ID(rhs.name)))))
		self.fail_if_null(out.name)

	def inplace_floor_divide(self, rhs, out):
		out.xdecref()
		self.v.ctx.add(c.Assignment('=', c.ID(out.name), c.FuncCall(c.ID('PyNumber_InPlaceFloorDivide'), c.ExprList(c.ID(self.name), c.ID(rhs.name)))))
		self.fail_if_null(out.name)

	def inplace_modulus(self, rhs, out):
		out.xdecref()
		self.v.ctx.add(c.Assignment('=', c.ID(out.name), c.FuncCall(c.ID('PyNumber_InPlaceRemainder'), c.ExprList(c.ID(self.name), c.ID(rhs.name)))))
		self.fail_if_null(out.name)

	def inplace_power(self, rhs, out):
		out.xdecref()
		self.v.ctx.add(c.Assignment('=', c.ID(out.name), c.FuncCall(c.ID('PyNumber_InPlacePower'), c.ExprList(c.ID(self.name), c.ID(rhs.name), c.ID(self.v.none.name)))))
		self.fail_if_null(out.name)
	## END Inplace Binary Ops ##


	## Unary Ops ##
	def invert(self, out):
		out.xdecref()
		self.v.ctx.add(c.Assignment('=', c.ID(out.name), c.FuncCall(c.ID('PyNumber_Invert'), c.ExprList(c.ID(self.name)))))
		self.fail_if_null(out.name)


	def positive(self, out):
		out.xdecref()
		self.v.ctx.add(c.Assignment('=', c.ID(out.name), c.FuncCall(c.ID('PyNumber_Positive'), c.ExprList(c.ID(self.name)))))
		self.fail_if_null(out.name)


	def negative(self, out):
		out.xdecref()
		self.v.ctx.add(c.Assignment('=', c.ID(out.name), c.FuncCall(c.ID('PyNumber_Negative'), c.ExprList(c.ID(self.name)))))
		self.fail_if_null(out.name)


	def not_(self, out_inst=None):
		if not out_inst:
			out_inst = CIntegerLL(None, self.v)
			out_inst.declare(name="_not_rv")
		assert isinstance(out_inst, CIntegerLL)
		self.v.ctx.add(c.Assignment('=', c.ID(out_inst.name), c.FuncCall(c.ID('PyObject_Not'), c.ExprList(c.ID(self.name)))))
		self.fail_if_negative(out_inst.name)
		return out_inst
	## END Unary Ops ##


	def is_true(self, out_inst=None):
		if not out_inst:
			out_inst = CIntegerLL(None, self.v)
			out_inst.declare(name="_istrue_rv")
		assert isinstance(out_inst, CIntegerLL)
		self.v.ctx.add(c.Assignment('=', c.ID(out_inst.name), c.FuncCall(c.ID('PyObject_IsTrue'), c.ExprList(c.ID(self.name)))))
		self.fail_if_negative(out_inst.name)
		return out_inst


	def rich_compare_bool(self, rhs, opid):
		out = CIntegerLL(None, self.v)
		out.declare()
		self.v.ctx.add(c.Assignment('=', c.ID(out.name), c.FuncCall(c.ID('PyObject_RichCompareBool'), c.ExprList(
																				c.ID(self.name), c.ID(rhs.name), c.ID(opid)))))
		self.fail_if_negative(out.name)
		return out


	### Mapping
	def mapping_size(self, out_inst=None):
		if not out_inst:
			out_inst = CIntegerLL(None, self.v)
			out_inst.declare(name='_size')
		self.v.ctx.add(c.Assignment('=', c.ID(out_inst.name), c.FuncCall(c.ID('PyMapping_Size'), c.ExprList(c.ID(self.name)))))
		self.fail_if_negative(out_inst.name)
		return out_inst

	def mapping_keys(self, out_inst=None):
		if not out_inst:
			out_inst = PyObjectLL(None, self.v)
			out_inst.declare(name='_keys')
		out_inst.xdecref()
		self.v.ctx.add(c.Assignment('=', c.ID(out_inst.name), c.FuncCall(c.ID('PyMapping_Keys'), c.ExprList(c.ID(self.name)))))
		self.fail_if_null(out_inst.name)
		return out_inst
	### End Mapping

	### Sequence
	def sequence_contains(self, item):
		out = CIntegerLL(None, self.v)
		out.declare()
		self.v.ctx.add(c.Assignment('=', c.ID(out.name), c.FuncCall(c.ID('PySequence_Contains'), c.ExprList(
																				c.ID(self.name), c.ID(item.name)))))
		self.fail_if_negative(out.name)
		return out


	def sequence_get_item(self, key, out_inst=None):
		if not out_inst:
			out_inst = PyObjectLL(None, self.v)
			out_inst.declare()
		out_inst.xdecref()
		self.v.ctx.add(c.Assignment('=', c.ID(out_inst.name), c.FuncCall(c.ID('PySequence_GetItem'), c.ExprList(
															c.ID(self.name), c.ID(key.name)))))
		self.fail_if_null(out_inst.name)
		return out_inst


	def sequence_inplace_concat(self, seq_inst, out_inst=None):
		if not out_inst:
			out_inst = PyObjectLL(None, self.v)
			out_inst.declare()
		out_inst.xdecref()
		self.v.ctx.add(c.Assignment('=', c.ID(out_inst.name), c.FuncCall(c.ID('PySequence_InPlaceConcat'), c.ExprList(c.ID(self.name), c.ID(seq_inst.name)))))
		self.fail_if_null(out_inst.name)
		return out_inst


	def sequence_as_tuple(self, out_inst=None):
		if not out_inst:
			out_inst = PyTupleLL(None, self.v)
			out_inst.declare()
		out_inst.xdecref()
		self.v.ctx.add(c.Assignment('=', c.ID(out_inst.name), c.FuncCall(c.ID('PySequence_Tuple'), c.ExprList(c.ID(self.name)))))
		return out_inst


	def sequence_get_slice(self, start, end, step, out_inst=None):
		'''Extract a sequence from this sequence which is a slice of this sequence.'''
		# Case 0: no step -> just call GetSlice with ints
		if step is None:
			if not out_inst:
				out_inst = PyObjectLL(None, self.v)
				out_inst.declare(name='_sliced')

			if start is None: _start = c.Constant('integer', 0)
			else: _start = c.ID(start.as_ssize().name)
			if end is None: _end = c.Constant('integer', CIntegerLL.MAX)
			else: _end = c.ID(end.as_ssize().name)

			self.v.ctx.add(c.Assignment('=', c.ID(out_inst.name), c.FuncCall(c.ID('PySequence_GetSlice'), c.ExprList(c.ID(self.name), _start, _end))))
			self.fail_if_null(out_inst.name)

		# Case 1: have a step -> create a new Slice with PyObject's, use that to get item
		else:
			slice_inst = PySliceLL(None, self.v)
			slice_inst.declare(name='_slice')

			if start is None: _start = self.v.none; _start.incref()
			else: _start = start.as_pyobject()
			if end is None: _end = self.v.none; _end.incref()
			else: _end = end.as_pyobject()
			_step = step.as_pyobject()

			slice_inst.new(_start, _end, _step)

			out_inst = self.get_item(slice_inst, out_inst)

		return out_inst


	def sequence_set_slice(self, start, end, step, src_inst):
		'''Assign a sequence into a sliced sequence.'''
		# Case 0: no step means we can use the fast sequence SetSlice
		if step is None:
			out_inst = CIntegerLL(None, self.v)
			out_inst.declare(name='_rv_slice')

			if start is None: _start = c.Constant('integer', 0)
			else: _start = c.ID(start.as_ssize().name)
			if end is None: _end = c.Constant('integer', CIntegerLL.MAX)
			else: _end = c.ID(end.as_ssize().name)

			self.v.ctx.add(c.Assignment('=', c.ID(out_inst.name), c.FuncCall(c.ID('PySequence_SetSlice'),
																			c.ExprList(c.ID(self.name), _start, _end, c.ID(src_inst.name)))))
			self.fail_if_negative(out_inst.name)

		else:
			slice_inst = PySliceLL(None, self.v)
			slice_inst.declare(name='_slice')

			if start is None: _start = self.v.none; _start.incref()
			else: _start = start.as_pyobject()
			if end is None: _end = self.v.none; _end.incref()
			else: _end = end.as_pyobject()
			_step = step.as_pyobject()

			slice_inst.new(_start, _end, _step)

			out_inst = self.set_item(slice_inst, src_inst)

		return out_inst


	def sequence_del_slice(self,
						start:int or CIntegerLL,
						end:int or CIntegerLL,
						step:int or CIntegerLL):
		out = CIntegerLL(None, self.v)
		out.declare()
		_start = c.Constant('integer', start) if isinstance(start, int) else c.ID(start.name)
		_end = c.Constant('integer', end) if isinstance(end, int) else c.ID(end.name)
		if step != 1:
			raise NotImplementedError("Slicing with a step size is not yet supported")
		self.v.ctx.add(c.Assignment('=', c.ID(out.name), c.FuncCall(c.ID('PySequence_DelSlice'), c.ExprList(c.ID(self.name), _start, _end))))
		self.fail_if_nonzero(out.name)
		return out
	### End Sequence


	def is_(self, other):
		out = CIntegerLL(None, self.v)
		out.declare()
		self.v.ctx.add(c.Assignment('=', c.ID(out.name), c.BinaryOp('==', c.ID(self.name), c.ID(other.name))))
		return out


	def get_iter(self, iter):
		iter.xdecref()
		self.v.ctx.add(c.Assignment('=', c.ID(iter.name), c.FuncCall(c.ID('PyObject_GetIter'), c.ExprList(c.ID(self.name)))))
		self.fail_if_null(iter.name)


	def get_type(self, out):
		assert isinstance(out, PyTypeLL)
		out.xdecref()
		self.v.ctx.add(c.Assignment('=', c.ID(out.name), c.FuncCall(c.ID('PyObject_Type'), c.ExprList(c.ID(self.name)))))
		self.fail_if_null(out.name)


	def as_ssize(self, out=None):
		if not out:
			out = CIntegerLL(None, self.v)
			out.declare()
		assert isinstance(out, CIntegerLL)
		self.v.ctx.add(c.Assignment('=', c.ID(out.name), c.FuncCall(c.ID('PyNumber_AsSsize_t'), c.ExprList(c.ID(self.name), c.ID('PyExc_OverflowError')))))
		self.fail_if_error_occurred()
		return out


	def is_instance(self, type_type):
		out = CIntegerLL(None, self.v)
		out.declare()
		self.v.ctx.add(c.Assignment('=', c.ID(out.name), c.FuncCall(c.ID('PyObject_IsInstance'), c.ExprList(
									c.ID(self.name), c.Cast(PyObjectLL.typedecl(), c.UnaryOp('&', c.ID(type_type.typename())))))))
		self.fail_if_negative(out.name)
		return out


from melano.c.types.integer import CIntegerLL
from melano.c.types.pyslice import PySliceLL
from melano.c.types.pystring import PyStringLL
from melano.c.types.pytuple import PyTupleLL
from melano.c.types.pytype import PyTypeLL
