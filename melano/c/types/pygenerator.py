'''
Copyright (c) 2011, Terrence Cole.
All rights reserved.
'''
from melano.c import ast as c
from melano.c.types.pyfunction import PyFunctionLL
from melano.c.types.pyobject import PyObjectLL
from melano.c.types.pystring import PyStringLL


class PyGeneratorLL(PyFunctionLL):
	def create_runnerfunc(self, tu, args, vararg, kwonlyargs, kwarg):
		param_list = c.ParamList(c.Decl('gen_args', c.PtrDecl(c.TypeDecl('gen_args', c.IdentifierType('void')))))
		return_ty = c.TypeDecl(None, c.IdentifierType('void'))
		self._create_runner_common(tu, param_list, return_ty)


	def runner_load_args(self, ctx, args, vararg, kwonlyargs, kwarg):
		args = self._buildargs(args, vararg, kwonlyargs, kwarg)

		ctx.add(c.Decl('py_gen_args', c.PtrDecl(c.PtrDecl(c.TypeDecl('gen_args', c.IdentifierType('PyObject'))))))
		ctx.add(c.Assignment('=', c.ID('py_gen_args'), c.ID('gen_args')))

		inst = PyObjectLL(None, self.visitor)
		inst.declare(self.visitor.scope.context, name='__self__')
		ctx.add(c.Assignment('=', c.ID(inst.name), c.ArrayRef(c.ID('py_gen_args'), c.Constant('integer', 0))))

		for i, arg in enumerate(args):
			#arg_inst = self.visitor.create_ll_instance(arg.arg.hl)
			#arg_inst.name = str(arg.arg)
			#self.locals_map[str(arg.arg)] = str(arg.arg)

			ctx.add(c.Comment("set arg '{}'".format(str(arg.arg))))
			inst = PyObjectLL(arg.arg.hl, self.visitor)
			#inst.name = str(arg.arg)
			inst.declare(ctx.visitor.scope.context)
			ctx.add(c.Assignment('=', c.ID(inst.name), c.ArrayRef(c.ID('py_gen_args'), c.Constant('integer', i + 2))))
			self.locals_map[str(arg.arg)] = str(arg.arg)



	def transfer_to_runnerfunc(self, ctx, args, vararg, kwonlyargs, kwarg):
		args = self._buildargs_idlist(args, vararg, kwonlyargs, kwarg)

		## PyObject **tmp = calloc(sizeof(PyObject*), <len(args)> + 2)
		#0: set to the generator object itself
		#1: used as a slot to communicate a yielded value
		#2+: args in canonical order
		argsname = ctx.visitor.scope.context.reserve_name('gen_argslist')
		decl = c.Decl(argsname, c.PtrDecl(PyObjectLL.typedecl()), init=c.ID('NULL'))
		ctx.visitor.scope.context.add_variable(decl)
		ctx.cleanup.remove(argsname) # not a pyobject and not for cleanup here
		ctx.add(c.Assignment('=', c.ID(argsname), c.FuncCall(c.ID('calloc'), c.ExprList(c.Constant('integer', len(args) + 2),
																					c.FuncCall(c.ID('sizeof'), c.ExprList(PyObjectLL.typedecl()))))))
		self.fail_if_null(ctx, argsname)
		ctx.add(c.Assignment('=', c.ArrayRef(c.ID(argsname), c.Constant('integer', 0)), c.ID('NULL')))
		ctx.add(c.Assignment('=', c.ArrayRef(c.ID(argsname), c.Constant('integer', 1)), c.ID('NULL')))
		for i, argid in enumerate(args):
			ctx.add(c.Assignment('=', c.ArrayRef(c.ID(argsname), c.Constant('integer', i + 2)), argid))
			ctx.add(c.FuncCall(c.ID('Py_XINCREF'), c.ExprList(argid)))

		ctx.add(c.Assignment('=', c.ID('__return_value__'), c.FuncCall(c.ID('MelanoGen_New'), c.ExprList(
												c.FuncCall(c.ID('strdup'), c.ExprList(c.Constant('string', PyStringLL.str2c(self.hlnode.owner.name)))),
												c.ID(self.c_runner_func.decl.name),
												c.ID(argsname),
												c.Constant('integer', 4096), #FIXME: try to discover and set a good size for the stack
												c.ID('NULL')
											))))
		self.fail_if_null(ctx, '__return_value__')
		ctx.add(c.FuncCall(c.ID('Py_INCREF'), c.ExprList(c.ID('__return_value__'))))
		ctx.add(c.Assignment('=', c.ArrayRef(c.ID(argsname), c.Constant('integer', 0)), c.ID('__return_value__')))


	def runner_outro(self, ctx):
		super().runner_outro(ctx)
		del ctx.block_items[-1]
		ctx.add(c.Assignment('=', c.ArrayRef(c.ID('py_gen_args'), c.Constant('integer', 1)), c.ID('NULL')))
		ctx.add(c.FuncCall(c.ID('coro_transfer'), c.ExprList(
																	c.FuncCall(c.ID('MelanoGen_GetContext'), c.ExprList(c.ArrayRef(c.ID('py_gen_args'), c.Constant('integer', 0)))),
																	c.FuncCall(c.ID('MelanoGen_GetSourceContext'), c.ExprList(c.ArrayRef(c.ID('py_gen_args'), c.Constant('integer', 0))))
																	)))
