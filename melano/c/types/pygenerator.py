'''
Copyright (c) 2011, Terrence Cole.
All rights reserved.
'''
from melano.c import ast as c
from melano.c.types.integer import CIntegerLL
from melano.c.types.pyfunction import PyFunctionLL
from melano.c.types.pyobject import PyObjectLL
from melano.c.types.pystring import PyStringLL


class PyGeneratorLL(PyFunctionLL):
	SELF_INDEX = 0
	GENERATOR_INDEX = 1
	RETURN_INDEX = 2
	ARGS_INDEX = 3


	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.args_name = None
		self.self_inst = None
		self.gen_inst = None


	def create_runnerfunc(self, tu, args, vararg, kwonlyargs, kwarg):
		body = c.Compound()
		body.visitor = self.visitor
		body.reserve_name('gen_args')

		# create ll insts and declare all args here to match normal functions decl order
		for arg in args:
			ll_inst = self.visitor.create_ll_instance(arg.arg.hl)
			ll_inst.declare(self.visitor.scope.context)
		if vararg:
			ll_inst = self.visitor.create_ll_instance(vararg.hl)
			ll_inst.declare(self.visitor.scope.context)
		for arg in kwonlyargs:
			ll_inst = self.visitor.create_ll_instance(arg.arg.hl)
			ll_inst.declare(self.visitor.scope.context)
		if kwarg:
			ll_inst = self.visitor.create_ll_instance(kwarg.hl)
			ll_inst.declare(self.visitor.scope.context)


		param_list = c.ParamList(c.Decl('gen_args', c.PtrDecl(c.TypeDecl('gen_args', c.IdentifierType('void')))))
		return_ty = c.TypeDecl(None, c.IdentifierType('void'))
		self._create_runner_common(tu, param_list, return_ty, body)


	def transfer_to_runnerfunc(self, ctx, args, vararg, kwonlyargs, kwarg):
		args = self._buildargs_idlist(args, vararg, kwonlyargs, kwarg)

		## PyObject **tmp = calloc(sizeof(PyObject*), <len(args)> + 2)
		#0: set to the function object
		#1: set to the generator object itself
		#2: used as a slot to communicate a yielded value
		#3+: args in canonical order
		argsname = self.visitor.scope.context.reserve_name('gen_argslist')
		decl = c.Decl(argsname, c.PtrDecl(PyObjectLL.typedecl()), init=c.ID('NULL'))
		self.visitor.scope.context.add_variable(decl, False)
		ctx.add(c.Assignment('=', c.ID(argsname), c.FuncCall(c.ID('calloc'), c.ExprList(c.Constant('integer', len(args) + 3),
																					c.FuncCall(c.ID('sizeof'), c.ExprList(PyObjectLL.typedecl()))))))
		self.fail_if_null(ctx, argsname)
		ctx.add(c.Assignment('=', c.ArrayRef(c.ID(argsname), c.Constant('integer', self.SELF_INDEX)), c.ID('self')))
		ctx.add(c.Assignment('=', c.ArrayRef(c.ID(argsname), c.Constant('integer', self.GENERATOR_INDEX)), c.ID('NULL')))
		ctx.add(c.Assignment('=', c.ArrayRef(c.ID(argsname), c.Constant('integer', self.RETURN_INDEX)), c.ID('NULL')))
		for i, argid in enumerate(args, self.ARGS_INDEX):
			ctx.add(c.Assignment('=', c.ArrayRef(c.ID(argsname), c.Constant('integer', i)), argid))
			ctx.add(c.FuncCall(c.ID('Py_XINCREF'), c.ExprList(argid)))

		ctx.add(c.Assignment('=', c.ID('__return_value__'), c.FuncCall(c.ID('MelanoGen_New'), c.ExprList(
												c.FuncCall(c.ID('strdup'), c.ExprList(c.Constant('string', PyStringLL.str2c(self.hlnode.owner.name)))),
												c.ID(self.c_runner_func.decl.name),
												c.ID(argsname),
												c.Constant('integer', 4096) #FIXME: try to discover and set a good size for the stack
											))))
		self.fail_if_null(ctx, '__return_value__')
		ctx.add(c.FuncCall(c.ID('Py_INCREF'), c.ExprList(c.ID('__return_value__'))))
		ctx.add(c.Assignment('=', c.ArrayRef(c.ID(argsname), c.Constant('integer', self.GENERATOR_INDEX)), c.ID('__return_value__')))


	def runner_load_args(self, ctx, args, vararg, kwonlyargs, kwarg):
		arg_list = self._buildargs(args, vararg, kwonlyargs, kwarg)

		for offset, arg in enumerate(arg_list, self.ARGS_INDEX):
			ctx.add(c.Comment("set arg '{}'".format(str(arg.arg))))
			inst = PyObjectLL(arg.arg.hl, self.visitor)
			inst.declare(self.visitor.scope.context)
			ctx.add(c.Assignment('=', c.ID(inst.name), c.ArrayRef(c.ID(self.args_name), c.Constant('integer', offset))))
			inst.incref(ctx)
			self.locals_map[str(arg.arg)] = str(arg.arg)
			self.args_pos_map.append(str(arg.arg))


	def runner_intro(self, ctx):
		'''Set the generator context on the TLS so that we can get to it from generators we call into.'''
		ctx.add(c.Comment('cast args to PyObject**'))
		self.args_name = ctx.reserve_name('__args__')
		ctx.add_variable(c.Decl(self.args_name, c.PtrDecl(c.PtrDecl(c.TypeDecl(self.args_name, c.IdentifierType('PyObject')))), init=c.ID('NULL')), False)
		ctx.add(c.Assignment('=', c.ID(self.args_name), c.Cast(c.PtrDecl(PyObjectLL.typedecl()), c.ID('gen_args'))))
		self.fail_if_null(ctx, self.args_name)

		ctx.add(c.Comment('get function instance'))
		self.self_inst = PyObjectLL(None, self.visitor)
		self.self_inst.declare(self.visitor.scope.context, name='__self__')
		ctx.add(c.Assignment('=', c.ID(self.self_inst.name), c.ArrayRef(c.ID(self.args_name), c.Constant('integer', self.SELF_INDEX))))
		self.fail_if_null(ctx, self.self_inst.name)
		self.self_inst.incref(ctx)

		ctx.add(c.Comment('get generator instance'))
		self.gen_inst = PyObjectLL(None, self.visitor)
		self.gen_inst.declare(self.visitor.scope.context, name='__gen__')
		ctx.add(c.Assignment('=', c.ID(self.gen_inst.name), c.ArrayRef(c.ID(self.args_name), c.Constant('integer', self.GENERATOR_INDEX))))
		self.fail_if_null(ctx, self.gen_inst.name)
		self.gen_inst.incref(ctx)

		super().runner_intro(ctx)

		ctx.add(c.Comment('mark us as in the generator'))
		tmp = CIntegerLL(None, self.visitor)
		tmp.declare(self.visitor.scope.context)
		ctx.add(c.Assignment('=', c.ID(tmp.name), c.FuncCall(c.ID('MelanoGen_EnterContext'), c.ExprList(c.ID('__self__')))))
		self.fail_if_nonzero(ctx, tmp.name)


	def runner_outro(self, ctx):
		'''In order to leave a coroutine, we set the return context to NULL and transfer back.  The generator will
			raise a StopError in the owning context for us.  We also need to pop our generator context.'''
		super().runner_outro(ctx)
		del ctx.block_items[-1]

		tmp = CIntegerLL(None, self.visitor)
		tmp.declare(self.visitor.scope.context)
		ctx.add(c.Assignment('=', c.ID(tmp.name), c.FuncCall(c.ID('MelanoGen_LeaveContext'), c.ExprList(c.ID(self.self_inst.name)))))
		self.fail_if_nonzero(ctx, tmp.name)

		ctx.add(c.Assignment('=', c.ArrayRef(c.ID(self.args_name), c.Constant('integer', self.RETURN_INDEX)), c.ID('NULL')))
		ctx.add(c.FuncCall(c.ID('coro_transfer'), c.ExprList(
																	c.FuncCall(c.ID('MelanoGen_GetContext'), c.ExprList(c.ID(self.gen_inst.name))),
																	c.FuncCall(c.ID('MelanoGen_GetSourceContext'), c.ExprList(c.ID(self.gen_inst.name)))
																	)))

	def do_yield(self, ctx, rv_inst):
		# assign to our yielded slot slot
		if not rv_inst:
			rv_inst = self.visitor.none
		ctx.add(c.Assignment('=', c.ArrayRef(c.ID(self.args_name), c.Constant('integer', self.RETURN_INDEX)), c.ID(rv_inst.name)))
		rv_inst.incref(ctx)


		# transfer control back to originator
		ctx.add(c.FuncCall(c.ID('MelanoGen_LeaveContext'), c.ExprList(c.ID(self.self_inst.name))))
		ctx.add(c.FuncCall(c.ID('coro_transfer'), c.ExprList(
																	c.FuncCall(c.ID('MelanoGen_GetContext'), c.ExprList(c.ID(self.gen_inst.name))),
																	c.FuncCall(c.ID('MelanoGen_GetSourceContext'), c.ExprList(c.ID(self.gen_inst.name)))
																	)))
		ctx.add(c.FuncCall(c.ID('MelanoGen_EnterContext'), c.ExprList(c.ID(self.self_inst.name))))

		# set yielded slot to null
		ctx.add(c.Assignment('=', c.ArrayRef(c.ID(self.args_name), c.Constant('integer', self.RETURN_INDEX)), c.ID('NULL')))
