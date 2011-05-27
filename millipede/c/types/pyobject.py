'''
Copyright (c) 2011, Terrence Cole.
All rights reserved.
'''
from millipede.c import ast as c
from millipede.c.types.lltype import LLType


class PyObjectLL(LLType):
	@staticmethod
	def typename():
		return 'PyObject'

	@staticmethod
	def typedecl(name=None):
		return c.PtrDecl(c.TypeDecl(name, c.IdentifierType('PyObject')))


	def declare_tmp(self, *, name=None):
		need_declare = super().declare_tmp(name=name)
		if need_declare:
			self.v.scope.ctx.add_variable(c.Decl(self.name, self.typedecl(self.name)), need_cleanup=False)


	def declare(self, *, is_global=False, quals=[], name=None):
		super().declare(is_global=is_global, quals=quals, name=name)
		ctx = self.v.tu if is_global else self.v.scope.ctx
		#ctx.add_variable(c.Decl(self.name, self.typedecl(self.name), quals=quals, init=c.ID('NULL')))
		ctx.add_variable(c.Decl(self.name, self.typedecl(self.name), quals=quals, init=c.ID('NULL')), need_cleanup=True)


	def new(self):
		self.tmp_incref()

	def incref(self):
		self.v.ctx.add(c.FuncCall(c.ID('Py_INCREF'), c.ID(self.name)))


	def xincref(self):
		self.v.ctx.add(c.FuncCall(c.ID('Py_XINCREF'), c.ID(self.name)))


	def decref(self):
		self.v.ctx.add(c.FuncCall(c.ID('Py_DECREF'), c.ID(self.name)))
		self.tmp_decref()
	def decref_only(self):
		'''Note: if we need to do a decref of a single variable in many different branches, we need to
			take account for the fact that we run both statically -- provide this so that we can keep our
			management structures until the last static decref.'''
		self.v.ctx.add(c.FuncCall(c.ID('Py_DECREF'), c.ID(self.name)))


	def xdecref(self):
		self.v.ctx.add(c.FuncCall(c.ID('Py_XDECREF'), c.ID(self.name)))
		self.tmp_decref()


	def clear(self):
		self.v.ctx.add(c.FuncCall(c.ID('Py_CLEAR'), c.ID(self.name)))
		self.tmp_decref()


	def as_pyobject(self):
		return self


	def str(self, out_inst=None):
		'''Convert to a string.'''
		if not out_inst:
			out_inst = PyStringLL(None, self.v)
			out_inst.declare_tmp(name="_str")
		self.v.ctx.add(c.Assignment('=', c.ID(out_inst.name), c.FuncCall(c.ID('PyObject_Str'), c.ExprList(c.ID(self.name)))))
		self.fail_if_null(out_inst.name)
		return out_inst


	def assign_none(self):
		self.v.none.incref()
		self.v.ctx.add(c.Assignment('=', c.ID(self.name), c.ID(self.v.none.name)))


	def assign_null(self):
		self.v.ctx.add(c.Assignment('=', c.ID(self.name), c.ID('NULL')))


	def assign_name(self, from_var):
		from_var = from_var.as_pyobject()
		from_var.xincref()
		self.v.ctx.add(c.Assignment('=', c.ID(self.name), c.ID(from_var.name)))


	def get_length(self, out_inst=None):
		if not out_inst:
			out_inst = CIntegerLL(None, self.v)
			out_inst.declare_tmp(name="_len")
		self.v.ctx.add(c.Assignment('=', c.ID(out_inst.name), c.FuncCall(c.ID('PyObject_Length'), c.ExprList(c.ID(self.name)))))
		self.fail_if_negative(out_inst.name)
		return out_inst


	def get_attr_string(self, attrname, out_var):
		self.v.ctx.add(c.Assignment('=', c.ID(out_var.name), c.FuncCall(c.ID('PyObject_GetAttrString'), c.ExprList(
														c.ID(self.name), c.Constant('string', attrname)))))
		self.fail_if_null(out_var.name)


	def get_attr_string_with_exception(self, attrname, out_var, exc_name, exc_str=None):
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
		tmp.declare_tmp(name="_setattr_rv")
		attrval = attrval.as_pyobject()
		self.v.ctx.add(c.Assignment('=', c.ID(tmp.name), c.FuncCall(c.ID('PyObject_SetAttrString'), c.ExprList(
															c.ID(self.name), c.Constant('string', attrname), c.ID(attrval.name)))))
		self.fail_if_nonzero(tmp.name)
		tmp.decref()


	def set_attr(self, attr, val):
		tmp = CIntegerLL(None, self.v)
		tmp.declare_tmp()
		self.v.ctx.add(c.Assignment('=', c.ID(tmp.name), c.FuncCall(c.ID('PyObject_SetAttr'), c.ExprList(
															c.ID(self.name), c.ID(attr.name), c.ID(val.name)))))
		self.fail_if_nonzero(tmp.name)
		tmp.decref()


	def del_attr_string(self, attrname):
		tmp = CIntegerLL(None, self.v)
		tmp.declare_tmp()
		self.v.ctx.add(c.Assignment('=', c.ID(tmp.name), c.FuncCall(c.ID('PyObject_DelAttrString'), c.ExprList(
															c.ID(self.name), c.Constant('string', attrname)))))
		self.fail_if_nonzero(tmp.name)
		tmp.decref()


	def get_item(self, key, out_inst=None):
		if not out_inst:
			out_inst = PyObjectLL(None, self.v)
			out_inst.declare_tmp(name="_item")
		self.v.ctx.add(c.Assignment('=', c.ID(out_inst.name), c.FuncCall(c.ID('PyObject_GetItem'), c.ExprList(
															c.ID(self.name), c.ID(key.name)))))
		self.fail_if_null(out_inst.name)
		return out_inst


	def set_item(self, key, val):
		out = CIntegerLL(None, self.v)
		out.declare_tmp()
		self.v.ctx.add(c.Assignment('=', c.ID(out.name), c.FuncCall(c.ID('PyObject_SetItem'), c.ExprList(
															c.ID(self.name), c.ID(key.name), c.ID(val.name)))))
		self.fail_if_nonzero(out.name)
		out.decref()


	def del_item(self, key):
		out = CIntegerLL(None, self.v)
		out.declare_tmp()
		self.v.ctx.add(c.Assignment('=', c.ID(out.name), c.FuncCall(c.ID('PyObject_DelItem'), c.ExprList(
															c.ID(self.name), c.ID(key.name)))))
		self.fail_if_nonzero(out.name)
		out.decref()


	def call(self, posargs, kwargs, out_var):
		'''Returns the instance of the return value.'''
		posid = c.ID(posargs.name) if posargs else c.ID('NULL')
		kwid = c.ID(kwargs.name) if kwargs else c.ID('NULL')
		self.v.ctx.add(c.Assignment('=', c.ID(out_var.name), c.FuncCall(c.ID('PyObject_Call'), c.ExprList(c.ID(self.name), posid, kwid))))
		self.fail_if_null(out_var.name)


	## Binary Ops ##
	def bitor(self, rhs, out):
		self.v.ctx.add(c.Assignment('=', c.ID(out.name), c.FuncCall(c.ID('PyNumber_Or'), c.ExprList(c.ID(self.name), c.ID(rhs.name)))))
		self.fail_if_null(out.name)


	def bitxor(self, rhs, out):
		self.v.ctx.add(c.Assignment('=', c.ID(out.name), c.FuncCall(c.ID('PyNumber_Xor'), c.ExprList(c.ID(self.name), c.ID(rhs.name)))))
		self.fail_if_null(out.name)


	def bitand(self, rhs, out):
		self.v.ctx.add(c.Assignment('=', c.ID(out.name), c.FuncCall(c.ID('PyNumber_And'), c.ExprList(c.ID(self.name), c.ID(rhs.name)))))
		self.fail_if_null(out.name)


	def lshift(self, rhs, out):
		self.v.ctx.add(c.Assignment('=', c.ID(out.name), c.FuncCall(c.ID('PyNumber_Lshift'), c.ExprList(c.ID(self.name), c.ID(rhs.name)))))
		self.fail_if_null(out.name)


	def rshift(self, rhs, out):
		self.v.ctx.add(c.Assignment('=', c.ID(out.name), c.FuncCall(c.ID('PyNumber_Rshift'), c.ExprList(c.ID(self.name), c.ID(rhs.name)))))
		self.fail_if_null(out.name)


	def add(self, rhs, out):
		self.v.ctx.add(c.Assignment('=', c.ID(out.name), c.FuncCall(c.ID('PyNumber_Add'), c.ExprList(c.ID(self.name), c.ID(rhs.name)))))
		self.fail_if_null(out.name)


	def subtract(self, rhs, out):
		self.v.ctx.add(c.Assignment('=', c.ID(out.name), c.FuncCall(c.ID('PyNumber_Subtract'), c.ExprList(c.ID(self.name), c.ID(rhs.name)))))
		self.fail_if_null(out.name)


	def multiply(self, rhs, out):
		self.v.ctx.add(c.Assignment('=', c.ID(out.name), c.FuncCall(c.ID('PyNumber_Multiply'), c.ExprList(c.ID(self.name), c.ID(rhs.name)))))
		self.fail_if_null(out.name)


	def divide(self, rhs, out):
		self.v.ctx.add(c.Assignment('=', c.ID(out.name), c.FuncCall(c.ID('PyNumber_TrueDivide'), c.ExprList(c.ID(self.name), c.ID(rhs.name)))))
		self.fail_if_null(out.name)


	def floor_divide(self, rhs, out):
		self.v.ctx.add(c.Assignment('=', c.ID(out.name), c.FuncCall(c.ID('PyNumber_FloorDivide'), c.ExprList(c.ID(self.name), c.ID(rhs.name)))))
		self.fail_if_null(out.name)


	def modulus(self, rhs, out):
		self.v.ctx.add(c.Assignment('=', c.ID(out.name), c.FuncCall(c.ID('PyNumber_Remainder'), c.ExprList(c.ID(self.name), c.ID(rhs.name)))))
		self.fail_if_null(out.name)


	def power(self, rhs, out):
		self.v.ctx.add(c.Assignment('=', c.ID(out.name), c.FuncCall(c.ID('PyNumber_Power'), c.ExprList(c.ID(self.name), c.ID(rhs.name), c.ID(self.v.none.name)))))
		self.fail_if_null(out.name)
	## END Binary Ops ##


	## Inplace Binary Ops ##
	def inplace_bitor(self, rhs, out):
		self.v.ctx.add(c.Assignment('=', c.ID(out.name), c.FuncCall(c.ID('PyNumber_InPlaceOr'), c.ExprList(c.ID(self.name), c.ID(rhs.name)))))
		self.fail_if_null(out.name)

	def inplace_bitxor(self, rhs, out):
		self.v.ctx.add(c.Assignment('=', c.ID(out.name), c.FuncCall(c.ID('PyNumber_InPlaceXor'), c.ExprList(c.ID(self.name), c.ID(rhs.name)))))
		self.fail_if_null(out.name)

	def inplace_bitand(self, rhs, out):
		self.v.ctx.add(c.Assignment('=', c.ID(out.name), c.FuncCall(c.ID('PyNumber_InPlaceAnd'), c.ExprList(c.ID(self.name), c.ID(rhs.name)))))
		self.fail_if_null(out.name)

	def inplace_lshift(self, rhs, out):
		self.v.ctx.add(c.Assignment('=', c.ID(out.name), c.FuncCall(c.ID('PyNumber_InPlaceLshift'), c.ExprList(c.ID(self.name), c.ID(rhs.name)))))
		self.fail_if_null(out.name)

	def inplace_rshift(self, rhs, out):
		self.v.ctx.add(c.Assignment('=', c.ID(out.name), c.FuncCall(c.ID('PyNumber_InPlaceRshift'), c.ExprList(c.ID(self.name), c.ID(rhs.name)))))
		self.fail_if_null(out.name)

	def inplace_add(self, rhs, out):
		self.v.ctx.add(c.Assignment('=', c.ID(out.name), c.FuncCall(c.ID('PyNumber_InPlaceAdd'), c.ExprList(c.ID(self.name), c.ID(rhs.name)))))
		self.fail_if_null(out.name)

	def inplace_subtract(self, rhs, out):
		self.v.ctx.add(c.Assignment('=', c.ID(out.name), c.FuncCall(c.ID('PyNumber_InPlaceSubtract'), c.ExprList(c.ID(self.name), c.ID(rhs.name)))))
		self.fail_if_null(out.name)

	def inplace_multiply(self, rhs, out):
		self.v.ctx.add(c.Assignment('=', c.ID(out.name), c.FuncCall(c.ID('PyNumber_InPlaceMultiply'), c.ExprList(c.ID(self.name), c.ID(rhs.name)))))
		self.fail_if_null(out.name)

	def inplace_divide(self, rhs, out):
		self.v.ctx.add(c.Assignment('=', c.ID(out.name), c.FuncCall(c.ID('PyNumber_InPlaceTrueDivide'), c.ExprList(c.ID(self.name), c.ID(rhs.name)))))
		self.fail_if_null(out.name)

	def inplace_floor_divide(self, rhs, out):
		self.v.ctx.add(c.Assignment('=', c.ID(out.name), c.FuncCall(c.ID('PyNumber_InPlaceFloorDivide'), c.ExprList(c.ID(self.name), c.ID(rhs.name)))))
		self.fail_if_null(out.name)

	def inplace_modulus(self, rhs, out):
		self.v.ctx.add(c.Assignment('=', c.ID(out.name), c.FuncCall(c.ID('PyNumber_InPlaceRemainder'), c.ExprList(c.ID(self.name), c.ID(rhs.name)))))
		self.fail_if_null(out.name)

	def inplace_power(self, rhs, out):
		self.v.ctx.add(c.Assignment('=', c.ID(out.name), c.FuncCall(c.ID('PyNumber_InPlacePower'), c.ExprList(c.ID(self.name), c.ID(rhs.name), c.ID(self.v.none.name)))))
		self.fail_if_null(out.name)
	## END Inplace Binary Ops ##


	## Unary Ops ##
	def invert(self, out):
		self.v.ctx.add(c.Assignment('=', c.ID(out.name), c.FuncCall(c.ID('PyNumber_Invert'), c.ExprList(c.ID(self.name)))))
		self.fail_if_null(out.name)


	def positive(self, out):
		self.v.ctx.add(c.Assignment('=', c.ID(out.name), c.FuncCall(c.ID('PyNumber_Positive'), c.ExprList(c.ID(self.name)))))
		self.fail_if_null(out.name)


	def negative(self, out):
		self.v.ctx.add(c.Assignment('=', c.ID(out.name), c.FuncCall(c.ID('PyNumber_Negative'), c.ExprList(c.ID(self.name)))))
		self.fail_if_null(out.name)


	def not_(self, out_inst=None):
		if not out_inst:
			out_inst = CIntegerLL(None, self.v)
			out_inst.declare_tmp(name="_not_rv")
		assert isinstance(out_inst, CIntegerLL)
		self.v.ctx.add(c.Assignment('=', c.ID(out_inst.name), c.FuncCall(c.ID('PyObject_Not'), c.ExprList(c.ID(self.name)))))
		self.fail_if_negative(out_inst.name)
		return out_inst
	## END Unary Ops ##


	def is_true(self, out_inst=None):
		if not out_inst:
			out_inst = CIntegerLL(None, self.v)
			out_inst.declare_tmp(name="_istrue_rv")
		assert isinstance(out_inst, CIntegerLL)
		self.v.ctx.add(c.Assignment('=', c.ID(out_inst.name), c.FuncCall(c.ID('PyObject_IsTrue'), c.ExprList(c.ID(self.name)))))
		self.fail_if_negative(out_inst.name)
		return out_inst


	def rich_compare_bool(self, rhs, opid):
		out = CIntegerLL(None, self.v)
		out.declare_tmp(name='_cmp')
		self.v.ctx.add(c.Assignment('=', c.ID(out.name), c.FuncCall(c.ID('PyObject_RichCompareBool'), c.ExprList(
																				c.ID(self.name), c.ID(rhs.name), c.ID(opid)))))
		self.fail_if_negative(out.name)
		return out


	### Mapping
	def mapping_size(self, out_inst=None):
		if not out_inst:
			out_inst = CIntegerLL(None, self.v)
			out_inst.declare_tmp(name='_size')
		self.v.ctx.add(c.Assignment('=', c.ID(out_inst.name), c.FuncCall(c.ID('PyMapping_Size'), c.ExprList(c.ID(self.name)))))
		self.fail_if_negative(out_inst.name)
		return out_inst

	def mapping_keys(self, out_inst=None):
		if not out_inst:
			out_inst = PyObjectLL(None, self.v)
			out_inst.declare_tmp(name='_keys')
		out_inst.xdecref()
		self.v.ctx.add(c.Assignment('=', c.ID(out_inst.name), c.FuncCall(c.ID('PyMapping_Keys'), c.ExprList(c.ID(self.name)))))
		self.fail_if_null(out_inst.name)
		return out_inst
	### End Mapping

	### Sequence
	def sequence_contains(self, item):
		out = CIntegerLL(None, self.v)
		out.declare_tmp()
		self.v.ctx.add(c.Assignment('=', c.ID(out.name), c.FuncCall(c.ID('PySequence_Contains'), c.ExprList(
																				c.ID(self.name), c.ID(item.name)))))
		self.fail_if_negative(out.name)
		return out


	def sequence_get_item(self, key, out_inst=None):
		if not out_inst:
			out_inst = PyObjectLL(None, self.v)
			out_inst.declare_tmp()
		self.v.ctx.add(c.Assignment('=', c.ID(out_inst.name), c.FuncCall(c.ID('PySequence_GetItem'), c.ExprList(
															c.ID(self.name), c.ID(key.name)))))
		self.fail_if_null(out_inst.name)
		return out_inst


	def sequence_inplace_concat(self, seq_inst, out_inst=None):
		if not out_inst:
			out_inst = PyObjectLL(None, self.v)
			out_inst.declare_tmp()
		self.v.ctx.add(c.Assignment('=', c.ID(out_inst.name), c.FuncCall(c.ID('PySequence_InPlaceConcat'), c.ExprList(c.ID(self.name), c.ID(seq_inst.name)))))
		self.fail_if_null(out_inst.name)
		return out_inst


	def sequence_as_tuple(self, out_inst=None):
		if not out_inst:
			out_inst = PyTupleLL(None, self.v)
			out_inst.declare_tmp()
		self.v.ctx.add(c.Assignment('=', c.ID(out_inst.name), c.FuncCall(c.ID('PySequence_Tuple'), c.ExprList(c.ID(self.name)))))
		return out_inst


	def sequence_get_slice(self, start, end, step, out_inst=None):
		'''Extract a sequence from this sequence which is a slice of this sequence.'''
		# Case 0: no step -> just call GetSlice with ints
		if step is None:
			if not out_inst:
				out_inst = PyObjectLL(None, self.v)
				out_inst.declare_tmp(name='_sliced')

			if start is None: _start = c.Constant('integer', 0)
			else: _start = c.ID(start.as_ssize().name)
			if end is None: _end = c.Constant('integer', CIntegerLL.MAX)
			else: _end = c.ID(end.as_ssize().name)

			self.v.ctx.add(c.Assignment('=', c.ID(out_inst.name), c.FuncCall(c.ID('PySequence_GetSlice'), c.ExprList(c.ID(self.name), _start, _end))))
			self.fail_if_null(out_inst.name)

		# Case 1: have a step -> create a new Slice with PyObject's, use that to get item
		else:
			slice_inst = PySliceLL(None, self.v)
			slice_inst.declare_tmp(name='_slice')

			if start is None: _start = self.v.none; _start.incref()
			else: _start = start.as_pyobject()
			if end is None: _end = self.v.none; _end.incref()
			else: _end = end.as_pyobject()
			_step = step.as_pyobject()

			slice_inst.new(_start, _end, _step)
			out_inst = self.get_item(slice_inst)
			slice_inst.decref()

		return out_inst


	def sequence_set_slice(self, start, end, step, src_inst):
		'''Assign a sequence into a sliced sequence.'''
		# Case 0: no step means we can use the fast sequence SetSlice
		if step is None:
			tmp_inst = CIntegerLL(None, self.v)
			tmp_inst.declare_tmp(name='_rv_slice')

			if start is None: _start = c.Constant('integer', 0)
			else: _start = c.ID(start.as_ssize().name)
			if end is None: _end = c.Constant('integer', CIntegerLL.MAX)
			else: _end = c.ID(end.as_ssize().name)

			self.v.ctx.add(c.Assignment('=', c.ID(tmp_inst.name), c.FuncCall(c.ID('PySequence_SetSlice'),
																			c.ExprList(c.ID(self.name), _start, _end, c.ID(src_inst.name)))))
			self.fail_if_negative(tmp_inst.name)
			tmp_inst.decref()

		else:
			slice_inst = PySliceLL(None, self.v)
			slice_inst.declare_tmp(name='_slice')

			if start is None: _start = self.v.none; _start.incref()
			else: _start = start.as_pyobject()
			if end is None: _end = self.v.none; _end.incref()
			else: _end = end.as_pyobject()
			_step = step.as_pyobject()

			slice_inst.new(_start, _end, _step)
			self.set_item(slice_inst, src_inst)
			slice_inst.decref()


	def sequence_del_slice(self, start, end, step):
		if step is None:
			tmp_inst = CIntegerLL(None, self.v)
			tmp_inst.declare_tmp(name='_rv_slice')

			if start is None: _start = c.Constant('integer', 0)
			else: _start = c.ID(start.as_ssize().name)
			if end is None: _end = c.Constant('integer', CIntegerLL.MAX)
			else: _end = c.ID(end.as_ssize().name)

			self.v.ctx.add(c.Assignment('=', c.ID(tmp_inst.name), c.FuncCall(c.ID('PySequence_DelSlice'),
																			c.ExprList(c.ID(self.name), _start, _end))))
			self.fail_if_nonzero(tmp_inst.name)
			tmp_inst.decref()

		else:
			slice_inst = PySliceLL(None, self.v)
			slice_inst.declare_tmp(name='_slice')

			if start is None: _start = self.v.none; _start.incref()
			else: _start = start.as_pyobject()
			if end is None: _end = self.v.none; _end.incref()
			else: _end = end.as_pyobject()
			_step = step.as_pyobject()

			slice_inst.new(_start, _end, _step)
			self.del_item(slice_inst)
			slice_inst.decref()

	### End Sequence


	def is_(self, other):
		out = CIntegerLL(None, self.v)
		out.declare_tmp()
		self.v.ctx.add(c.Assignment('=', c.ID(out.name), c.BinaryOp('==', c.ID(self.name), c.ID(other.name))))
		return out


	def get_iter(self, iter):
		self.v.ctx.add(c.Assignment('=', c.ID(iter.name), c.FuncCall(c.ID('PyObject_GetIter'), c.ExprList(c.ID(self.name)))))
		self.fail_if_null(iter.name)


	def get_type(self, out):
		assert isinstance(out, PyTypeLL)
		self.v.ctx.add(c.Assignment('=', c.ID(out.name), c.FuncCall(c.ID('PyObject_Type'), c.ExprList(c.ID(self.name)))))
		self.fail_if_null(out.name)


	def as_ssize(self, out=None):
		if not out:
			out = CIntegerLL(None, self.v)
			out.declare_tmp()
		assert isinstance(out, CIntegerLL)
		self.v.ctx.add(c.Assignment('=', c.ID(out.name), c.FuncCall(c.ID('PyNumber_AsSsize_t'), c.ExprList(c.ID(self.name), c.ID('PyExc_OverflowError')))))
		self.fail_if_error_occurred()
		return out


	def is_instance(self, type_type):
		out = CIntegerLL(None, self.v)
		out.declare_tmp()
		self.v.ctx.add(c.Assignment('=', c.ID(out.name), c.FuncCall(c.ID('PyObject_IsInstance'), c.ExprList(
									c.ID(self.name), c.Cast(PyObjectLL.typedecl(), c.UnaryOp('&', c.ID(type_type.typename())))))))
		self.fail_if_negative(out.name)
		return out


from millipede.c.types.integer import CIntegerLL
from millipede.c.types.pyslice import PySliceLL
from millipede.c.types.pystring import PyStringLL
from millipede.c.types.pytuple import PyTupleLL
from millipede.c.types.pytype import PyTypeLL
