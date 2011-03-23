'''
Copyright (c) 2011, Terrence Cole.
All rights reserved.
'''
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
		- create in context with PyMelanoFunction_New
		- create a new stack (MelanoLocals**) of len(list(self.each_func_scope()))
		- copy from __locals__ of creator (should be local) to new array in positions 0->n-1
		- set the locals on the new function object
	PyStub:
		<same>
	Runner:
		- on entry, grab the "locals" out of __self__ and put into local __locals__
		- create a MelanoLocals* for this run of the function, set on __locals__ at position n
		- put all args into the new MelanoLocals array, no further decl required for locals
		- modified get/set attribute to assign into the locals according to the locals_map
	'''

	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)

		# the c instance representing the array of local variables
		self.locals_name = None

		# build the "locals" map:
		# The locals pointer contains all of the names accessible from the current function, not just the really locals.
		# The top level of indirection points to a set of PyObject*[] containing the locals for ourself and for all lower
		#	frames, in order.  Some variable names will mask others below them.  Since we can know this pattern
		#	of masking, inheritance, etc statically, we discover this here and encode the info into variable accesses
		#	that are made in this scope.
		self.locals_map = {} # {str: (int, int)}
		for i, scope in enumerate(reversed(list(self.each_func_scope()))):
			names = list(scope.symbols.keys())
			for j, name in enumerate(names):
				sym = scope.symbols[name]
				if not isinstance(sym, NameRef):
					self.locals_map[name] = (i, j)


	@staticmethod
	def locals_typedecl(name=None):
		#return c.PtrDecl(c.PtrDecl(c.PtrDecl(c.TypeDecl(name, c.IdentifierType('PyObject')))))
		return c.PtrDecl(c.PtrDecl(c.TypeDecl(name, c.IdentifierType('MelanoLocals'))))

	@staticmethod
	def local_array_typedecl(name=None):
		return c.PtrDecl(c.TypeDecl(name, c.IdentifierType('MelanoLocals')))


	def each_func_scope(self):
		cur = self.hlnode
		while cur:
			if isinstance(cur, MelanoFunction):
				yield cur
			cur = cur.owner.parent


	def create_funcdef(self, ctx, tu, docstring):
		# create in context with PyMelanoFunction_New
		super().create_funcdef(ctx, tu, docstring)

		fn_scopes = list(self.each_func_scope())

		# create a new stack (MelanoLocals **) of len(list(self.each_func_scope()))
		# e.g. foo_locals = MelanoLocals_Create( len(list(fn_scopes)) )
		locals_name = self.visitor.scope.context.reserve_name(self.hlnode.owner.name + '_locals')
		ctx.add_variable(c.Decl(locals_name, self.locals_typedecl(locals_name)), False)
		ctx.add(c.Assignment('=', c.ID(locals_name), c.FuncCall(c.ID('MelanoStack_Create'), c.ExprList(
																									c.Constant('integer', len(fn_scopes))))))
		self.fail_if_null(ctx, locals_name)

		# copy from __locals__ of creator (should be local) to new array in positions 0 -> n - 1
		# e.g. MelanoStack_SetLocals(locals_name, lvl, __locals__[lvl]) 
		for i in range(len(fn_scopes[:-1])):
			ctx.add(c.FuncCall(c.ID('MelanoStack_SetLocals'), c.ExprList(
																		c.ID(locals_name),
																		c.Constant('integer', i),
																		c.ArrayRef(c.ID('__locals__'), c.Constant('integer', i)))))

		# set the locals on the new function object
		ctx.add(c.FuncCall(c.ID('PyMelanoFunction_SetLocals'), c.ExprList(
																		c.ID(self.c_obj.name),
																		c.ID(locals_name),
																		c.Constant('integer', len(fn_scopes)))))

		'''
		# malloc an array of PyObject** of len(list(self.each_func_scope()))
		locals_name = self.visitor.scope.context.reserve_name(self.hlnode.owner.name + '_locals')
		ctx.add_variable(c.Decl(locals_name, self.locals_typedecl(locals_name)), False)
		ctx.add(c.Assignment('=', c.ID(locals_name),
							c.Cast(self.locals_typedecl(),
									c.FuncCall(c.ID('calloc'), c.ExprList(c.Constant('integer', len(fn_scopes)),
											c.FuncCall(c.ID('sizeof'), c.ExprList(self.local_array_typedecl())))))))
		self.except_if_null(ctx, locals_name, 'PyExc_MemoryError')

		# copy from __locals__ of creator (should be local) to new array in positions 0->n-1
		for i in range(len(fn_scopes[:-1])):
			# locals_name[i] = __locals__[i]
			ctx.add(c.Assignment('=',
								c.ArrayRef(c.ID(locals_name), c.Constant('integer', i)),
								c.ArrayRef(c.ID('__locals__'), c.Constant('integer', i))))

		# malloc an array of PyObject* for our locals and fill it with NULL, assign to prior array at n
		local_name = self.visitor.scope.context.reserve_name(self.hlnode.owner.name + '_local')
		ctx.add_variable(c.Decl(local_name, self.local_array_typedecl(local_name)), False)
		ctx.add(c.Assignment('=', c.ID(local_name),
							c.Cast(self.local_array_typedecl(local_name),
								c.FuncCall(c.ID('calloc'), c.ExprList(c.Constant('integer', len(local_syms)),
														c.FuncCall(c.ID('sizeof'), c.ExprList(PyObjectLL.typedecl())))))))
		self.except_if_null(ctx, local_name, 'PyExc_MemoryError')
		ctx.add(c.Assignment('=', c.ArrayRef(c.ID(locals_name), c.Constant('integer', len(fn_scopes) - 1)), c.ID(local_name)))

		# set the locals on the new function object
		ctx.add(c.FuncCall(c.ID('PyMelanoFunction_SetLocals'), c.ExprList(c.ID(self.c_obj.name), c.ID(locals_name), c.Constant('integer', len(fn_scopes)))))
		'''

		return self.c_obj


	def runner_load_args(self, ctx, args, vararg, kwonlyargs, kwarg):
		fn_scopes = list(self.each_func_scope())
		local_syms = [(b, name) for name, (a, b) in self.locals_map.items() if a == len(fn_scopes) - 1]
		local_syms.sort()

		# on entry, grab the "locals" out of __self__ and put into local __locals__
		self.locals_name = self.visitor.scope.context.reserve_name('__locals__')
		ctx.add_variable(c.Decl(self.locals_name, self.locals_typedecl(self.locals_name)), False)
		ctx.add(c.Assignment('=', c.ID(self.locals_name),
							c.FuncCall(c.ID('PyMelanoFunction_GetLocals'), c.ExprList(c.ID('__self__')))))
		self.fail_if_null(ctx, self.locals_name)

		# create a MelanoLocals* for this run of the function, set on __locals__ at position n
		tmp_name = self.visitor.scope.context.reserve_name(self.hlnode.owner.name + '_ltmp')
		ctx.add_variable(c.Decl(tmp_name, self.local_array_typedecl(tmp_name)), False)
		ctx.add(c.Assignment('=', c.ID(tmp_name), c.FuncCall(c.ID('MelanoLocals_Create'), c.ExprList(c.Constant('integer', len(local_syms))))))
		self.fail_if_null(ctx, tmp_name)
		ctx.add(c.FuncCall(c.ID('MelanoStack_SetLocals'), c.ExprList(
															c.ID(self.locals_name),
															c.Constant('integer', len(fn_scopes) - 1),
															c.ID(tmp_name))))

		# put all args into the new MelanoLocals array, no further decl required for locals
		args = self._buildargs(args, vararg, kwonlyargs, kwarg)
		for i, arg in enumerate(args):
			ctx.add(c.Comment("set arg '{}'".format(str(arg.arg))))
			inst = PyObjectLL(arg.arg.hl, self.visitor)
			inst.name = str(arg.arg)
			self.set_attr_string(ctx, str(arg.arg), inst)

			#ctx.add(c.Assignment('=', c.ID(s), c.ArrayRef(c.ID('py_gen_args'), c.Constant('integer', i + 2))))


	def runner_load_locals(self, ctx):
		return


	def set_attr_string(self, ctx, attrname, val):
		i, j = self.locals_map[attrname]
		ref = c.ArrayRef(c.StructRef(c.ArrayRef(c.ID(self.locals_name), c.Constant('integer', i)), '->', c.ID('locals')), c.Constant('integer', j))
		ctx.add(c.FuncCall(c.ID('Py_XDECREF'), c.ExprList(ref)))
		ctx.add(c.FuncCall(c.ID('Py_INCREF'), c.ExprList(c.ID(val.name))))
		ctx.add(c.Assignment('=', ref, c.ID(val.name)))

		#ref = c.ArrayRef(c.ArrayRef(c.ID(self.locals_name), c.Constant('integer', i)), c.Constant('integer', j))
		#ctx.add(c.FuncCall(c.ID('Py_XDECREF'), c.ExprList(ref)))
		#ctx.add(c.FuncCall(c.ID('Py_INCREF'), c.ExprList(c.ID(val.name))))
		#ctx.add(c.Assignment('=', ref, c.ID(val.name)))
		pass


	def get_attr_string(self, ctx, attrname, outvar):
		i, j = self.locals_map[attrname]
		ref = c.ArrayRef(c.StructRef(c.ArrayRef(c.ID(self.locals_name), c.Constant('integer', i)), '->', c.ID('locals')), c.Constant('integer', j))
		ctx.add(c.Assignment('=', c.ID(outvar.name), ref))
		ctx.add(c.FuncCall(c.ID('Py_INCREF'), c.ExprList(c.ID(outvar.name))))

		#i, j = self.locals_map[attrname]
		#ctx.add(c.Assignment('=', c.ID(outvar.name),
		#					c.ArrayRef(
		#							c.ArrayRef(c.ID(self.locals_name), c.Constant('integer', i)),
		#							c.Constant('integer', j))))
		#ctx.add(c.FuncCall(c.ID('Py_INCREF'), c.ExprList(c.ID(outvar.name))))
		pass
