'''
Copyright (c) 2011, Terrence Cole.
All rights reserved.
'''
from contextlib import contextmanager
from melano.c import ast as c
from melano.c.types.integer import CIntegerLL
from melano.c.types.pydict import PyDictLL
from melano.c.types.pyfunction import PyFunctionLL
from melano.c.types.pyobject import PyObjectLL
from melano.hl.function import MelanoFunction
from melano.hl.nameref import NameRef


class PyClosureLL(PyFunctionLL):
	'''
	Calling proc:
	Creation:
		- create in context with MpFunction_New
		- create a new stack (MpStack*) of len(list(self.each_func_scope()))
		- copy from __locals__ of creator (should be local) to new array in positions 0->n-1
		- set the locals on the new function object
	PyStub:
		<same>
	Runner:
		- on entry, grab the "locals" out of __self__ and put into local __locals__
		- create a MpLocals* for this run of the function, set on __locals__ at position n
		- put all args into the new MpLocals array, no further decl required for locals
		- modified get/set attribute to assign into the locals according to the locals_map
		- on exit, free __locals__[n]
	Call Time:
		- before: nothing
		- after: restore __locals__[n], they may have been overridden by a recursive call 
	'''

	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)

		# the c instance representing the array of local variables
		self.stack_name = None
		self.locals_name = None


	@staticmethod
	def stack_typedecl(name=None):
		return c.PtrDecl(c.TypeDecl(name, c.IdentifierType('MpStack')))


	@staticmethod
	def locals_typedecl(name=None):
		return c.PtrDecl(c.TypeDecl(name, c.IdentifierType('MpLocals')))


	def each_func_scope(self):
		cur = self.hlnode
		while cur:
			if isinstance(cur, MelanoFunction):
				yield cur
			cur = cur.owner.parent


	def prepare(self):
		# build the "locals" map:
		# The locals pointer contains all of the names accessible from the current function, not just the really locals.
		# The top level of indirection points to a set of PyObject*[] containing the locals for ourself and for all lower
		#	frames, in order.  Some variable names will mask others below them.  Since we can know this pattern
		#	of masking, inheritance, etc statically, we discover this here and encode the info into variable accesses
		#	that are made in this scope.
		self.locals_map = {} # {str: (int, int)}
		for i, scope in enumerate(reversed(list(self.each_func_scope()))):
			names = list(scope.symbols.keys())
			local_names = [n for n in names if not isinstance(scope.symbols[n], NameRef)]
			for j, name in enumerate(local_names):
				self.locals_map[name] = (i, j)
		self.own_scope_offset = len(list(self.each_func_scope())) - 1


	def declare_function_object(self, docstring):
		# create in context with MpFunction_New
		super().declare_function_object(docstring)

		# create a new stack (MpStack *) of len(list(self.each_func_scope()))
		stack_name = self.v.scope.ctx.reserve_name(self.hlnode.owner.name + '_locals', self.v.tu)
		self.v.ctx.add_variable(c.Decl(stack_name, self.stack_typedecl(stack_name)), False)
		self.v.ctx.add(c.Assignment('=', c.ID(stack_name), c.FuncCall(c.ID('MpStack_Create'), c.ExprList(
																									c.Constant('integer', self.own_scope_offset + 1)))))
		self.fail_if_null(stack_name)

		# copy low levels of our __stack__ from our nearest parent ==> positions 0 -> n - 1
		# NOTE: if __stack__ is local, we are defined directly in our parent's scope, otherwise we need
		#		to lookup our parent's stack from the pycobject defined at the toplevel.
		if self.own_scope_offset > 0 and '__stack__' not in self.v.ctx.names:
			# declare a tmp for the parent's stack
			parent_stack = self.v.scope.ctx.tmpname(self.v.tu)
			self.v.scope.ctx.add_variable(c.Decl(parent_stack, self.stack_typedecl(parent_stack)), False)
			# lookup the next stack
			parent_scope = self.hlnode.get_next_scope()
			self.v.ctx.add(c.Assignment('=', c.ID(parent_stack), c.FuncCall(c.ID('MpFunction_GetStack'), c.ExprList(c.ID(parent_scope.ll.c_obj.name)))))
			c_parent_stack = c.ID(parent_stack)
		else:
			c_parent_stack = c.ID('__stack__')

		for i in range(self.own_scope_offset):
			self.v.ctx.add(c.FuncCall(c.ID('MpStack_SetLocals'), c.ExprList(
																		c.ID(stack_name),
																		c.Constant('integer', i),
																		c.ArrayRef(c_parent_stack, c.Constant('integer', i)))))

		# set the locals on the new function object
		self.v.ctx.add(c.FuncCall(c.ID('MpFunction_SetStack'), c.ExprList(
																		c.ID(self.c_obj.name),
																		c.ID(stack_name),
																		c.Constant('integer', self.own_scope_offset + 1))))

		return self.c_obj


	@contextmanager
	def maybe_recursive_call(self):
		yield
		self.v.ctx.add(c.FuncCall(c.ID('MpStack_RestoreLocals'), c.ExprList(
																c.ID(self.stack_name),
																c.Constant('integer', self.own_scope_offset),
																c.ID(self.locals_name))))

	def runner_intro(self):
		super().runner_intro()

		self.local_syms = [(b, name) for name, (a, b) in self.locals_map.items() if a == self.own_scope_offset]
		self.local_syms.sort()

		# on entry, grab the "stack" out of __self__ and put into local __stack__
		self.stack_name = self.v.scope.ctx.reserve_name('__stack__', self.v.tu)
		self.v.scope.ctx.add_variable(c.Decl(self.stack_name, self.stack_typedecl(self.stack_name)), False)
		self.v.ctx.add(c.Assignment('=', c.ID(self.stack_name),
							c.FuncCall(c.ID('MpFunction_GetStack'), c.ExprList(c.ID('__self__')))))
		self.fail_if_null(self.stack_name)

		# create a MpLocals* for this run of the function, set on __locals__ at position n
		self.locals_name = self.v.scope.ctx.reserve_name('__locals__', self.v.tu)
		self.v.scope.ctx.add_variable(c.Decl(self.locals_name, self.locals_typedecl(self.locals_name)), False)
		self.v.ctx.add(c.Assignment('=', c.ID(self.locals_name), c.FuncCall(c.ID('MpLocals_Create'), c.ExprList(c.Constant('integer', len(self.local_syms))))))
		self.fail_if_null(self.locals_name)
		self.v.ctx.add(c.FuncCall(c.ID('MpStack_SetLocals'), c.ExprList(
															c.ID(self.stack_name),
															c.Constant('integer', self.own_scope_offset),
															c.ID(self.locals_name))))


	def runner_load_args(self, args, vararg, kwonlyargs, kwarg):
		# put all args into the new MpLocals array, no further decl required for locals
		args = self._buildargs(args, vararg, kwonlyargs, kwarg)
		for i, arg in enumerate(args):
			self.v.ctx.add(c.Comment("set arg '{}'".format(str(arg.arg))))
			inst = PyObjectLL(arg.arg.hl, self.v)
			inst.name = str(arg.arg)
			self.set_attr_string(str(arg.arg), inst)


	def runner_load_locals(self):
		return


	def runner_outro(self):
		rv = super().runner_outro()
		fn_scopes = list(self.each_func_scope())
		self.v.ctx.block_items.insert(-1, c.FuncCall(c.ID('MpLocals_Destroy'), c.ExprList(
																					c.ID(self.stack_name), c.Constant('integer', len(fn_scopes) - 1))))
		return rv


	def del_attr_string(self, attrname):
		i, j = self.locals_map[attrname]
		ref = c.ArrayRef(c.StructRef(c.ArrayRef(c.ID(self.stack_name), c.Constant('integer', i)), '->', c.ID('locals')), c.Constant('integer', j))
		self.v.ctx.add(c.FuncCall(c.ID('Py_CLEAR'), c.ExprList(ref)))


	def set_attr_string(self, attrname, val):
		i, j = self.locals_map[attrname]
		ref = c.ArrayRef(c.StructRef(c.ArrayRef(c.ID(self.stack_name), c.Constant('integer', i)), '->', c.ID('locals')), c.Constant('integer', j))
		self.v.ctx.add(c.FuncCall(c.ID('Py_XDECREF'), c.ExprList(ref)))
		val = val.as_pyobject()
		val.incref()
		self.v.ctx.add(c.Assignment('=', ref, c.ID(val.name)))


	def get_attr_string(self, attrname, outvar):
		i, j = self.locals_map[attrname]
		outvar.xdecref()
		ref = c.ArrayRef(c.StructRef(c.ArrayRef(c.ID(self.stack_name), c.Constant('integer', i)), '->', c.ID('locals')), c.Constant('integer', j))
		self.v.ctx.add(c.Assignment('=', c.ID(outvar.name), ref))
		self.except_if_null(outvar.name, 'PyExc_UnboundLocalError', "local variable '{}' referenced before assignment".format(attrname))
		outvar.incref()


