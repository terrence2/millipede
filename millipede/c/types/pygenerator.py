'''
Copyright (c) 2011, Terrence Cole.
All rights reserved.
'''
from millipede.c import ast as c
from millipede.c.types.integer import CIntegerLL
from millipede.c.types.pyfunction import PyFunctionLL
from millipede.c.types.pyobject import PyObjectLL
from millipede.c.types.pystring import PyStringLL


class PyGeneratorLL(PyFunctionLL):
	SELF_INDEX = 0
	GENERATOR_INDEX = 1
	RETURN_INDEX = 2
	SEND_INDEX = 3
	ARGS_INDEX = 4

	N_EXTRA_PARAMS = 4

	STACKSIZE = 1024 * 1024 * 1

	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.args_name = None
		self.self_inst = None
		self.gen_inst = None


	def create_runnerfunc(self, args, vararg, kwonlyargs, kwarg):
		body = c.Compound()
		body.reserve_name('gen_args', self.v.tu)

		# create ll insts and declare all args here to match normal functions decl order
		for arg in args:
			ll_inst = self.v.create_ll_instance(arg.arg.hl)
			ll_inst.declare()
		if vararg:
			ll_inst = self.v.create_ll_instance(vararg.hl)
			ll_inst.declare()
		for arg in kwonlyargs:
			ll_inst = self.v.create_ll_instance(arg.arg.hl)
			ll_inst.declare()
		if kwarg:
			ll_inst = self.v.create_ll_instance(kwarg.hl)
			ll_inst.declare()


		param_list = c.ParamList(c.Decl('gen_args', c.PtrDecl(c.TypeDecl('gen_args', c.IdentifierType('void')))))
		return_ty = c.TypeDecl(None, c.IdentifierType('void'))
		self._create_runner_common(param_list, return_ty, body)


	def transfer_to_runnerfunc(self, args, vararg, kwonlyargs, kwarg):
		## PyObject **tmp = calloc(sizeof(PyObject*), <len(args)> + 2)
		#0: set to the function object
		#1: set to the generator object itself
		#2: used as a slot to communicate a yielded value
		#3+: args in canonical order
		argsname = self.v.scope.ctx.reserve_name('gen_argslist', self.v.tu)
		decl = c.Decl(argsname, c.PtrDecl(PyObjectLL.typedecl()), init=c.ID('NULL'))
		self.v.scope.ctx.add_variable(decl, False)
		self.v.ctx.add(c.Assignment('=', c.ID(argsname),
						c.FuncCall(c.ID('calloc'), c.ExprList(c.Constant('integer', self.N_EXTRA_PARAMS + len(self.stub_arg_insts)),
							c.FuncCall(c.ID('sizeof'), c.ExprList(PyObjectLL.typedecl()))))))
		self.fail_if_null(argsname)
		self.v.ctx.add(c.Assignment('=', c.ArrayRef(c.ID(argsname), c.Constant('integer', self.SELF_INDEX)), c.ID('self')))
		self.v.ctx.add(c.Assignment('=', c.ArrayRef(c.ID(argsname), c.Constant('integer', self.GENERATOR_INDEX)), c.ID('NULL')))
		self.v.ctx.add(c.Assignment('=', c.ArrayRef(c.ID(argsname), c.Constant('integer', self.RETURN_INDEX)), c.ID('NULL')))
		for i, arg_inst in enumerate(self.stub_arg_insts, self.ARGS_INDEX):
			self.v.ctx.add(c.Assignment('=', c.ArrayRef(c.ID(argsname), c.Constant('integer', i)), c.ID(arg_inst.name)))
			self.v.ctx.add(c.FuncCall(c.ID('Py_XINCREF'), c.ExprList(c.ID(arg_inst.name))))

		self.v.ctx.add(c.Assignment('=', c.ID('__return_value__'), c.FuncCall(c.ID('MpGenerator_New'), c.ExprList(
												c.FuncCall(c.ID('strdup'), c.ExprList(c.Constant('string', PyStringLL.name_to_c_string(self.hlnode.owner.name)))),
												c.ID(self.c_runner_func.decl.name),
												c.ID(argsname),
												c.Constant('integer', self.STACKSIZE) #FIXME: try to discover and set a good size for the stack
											))))
		self.fail_if_null('__return_value__')
		self.v.ctx.add(c.Assignment('=', c.ArrayRef(c.ID(argsname), c.Constant('integer', self.GENERATOR_INDEX)), c.ID('__return_value__')))


	def runner_load_args(self, args, vararg, kwonlyargs, kwarg):
		arg_list = self._buildargs(args, vararg, kwonlyargs, kwarg)

		#FIXME: do not re-declare here... maybe share this with pyfunction? 
		for offset, arg in enumerate(arg_list, self.ARGS_INDEX):
			#NOTE: incref happened in stub to preserve the value for us
			inst = PyObjectLL(arg.arg.hl, self.v)
			inst.declare()
			self.v.ctx.add(c.Assignment('=', c.ID(inst.name), c.ArrayRef(c.ID(self.args_name), c.Constant('integer', offset))))
			self.locals_map[str(arg.arg)] = str(arg.arg)
			self.args_pos_map.append(str(arg.arg))


	def runner_intro(self):
		'''Set the generator context on the TLS so that we can get to it from generators we call into.'''
		self.v.ctx.add(c.Comment('cast args to PyObject**'))
		self.args_name = self.v.scope.ctx.reserve_name('__args__', self.v.tu)
		self.v.scope.ctx.add_variable(c.Decl(self.args_name, c.PtrDecl(c.PtrDecl(c.TypeDecl(self.args_name, c.IdentifierType('PyObject')))), init=c.ID('NULL')), False)
		self.v.ctx.add(c.Assignment('=', c.ID(self.args_name), c.Cast(c.PtrDecl(PyObjectLL.typedecl()), c.ID('gen_args'))))
		self.fail_if_null(self.args_name)

		#NOTE: we should _not_ incref our __self__ or __gen__ since this function _is_ us -- if we keep this ref and don't 
		#  fully drain, then we will never decref ourself and clean up the other references we're holding onto

		self.v.ctx.add(c.Comment('get function instance'))
		self.self_inst = PyObjectLL(None, self.v)
		self.self_inst.declare_tmp(name='__self__')
		self.v.ctx.add(c.Assignment('=', c.ID(self.self_inst.name), c.ArrayRef(c.ID(self.args_name), c.Constant('integer', self.SELF_INDEX))))
		self.fail_if_null(self.self_inst.name)

		self.v.ctx.add(c.Comment('get generator instance'))
		self.gen_inst = PyObjectLL(None, self.v)
		self.gen_inst.declare_tmp(name='__gen__')
		self.v.ctx.add(c.Assignment('=', c.ID(self.gen_inst.name), c.ArrayRef(c.ID(self.args_name), c.Constant('integer', self.GENERATOR_INDEX))))
		self.fail_if_null(self.gen_inst.name)

		super().runner_intro()

		self.v.ctx.add(c.Comment('mark us as in the generator'))
		tmp = CIntegerLL(None, self.v)
		tmp.declare_tmp()
		self.v.ctx.add(c.Assignment('=', c.ID(tmp.name), c.FuncCall(c.ID('MpGenerator_EnterContext'), c.ExprList(c.ID(self.gen_inst.name)))))
		self.fail_if_nonzero(tmp.name)
		tmp.decref()


	def _runner_cleanup(self):
		'''Make sure to leave the __gen__ context before we decref it.'''
		self.v.ctx.add(c.FuncCall(c.ID('MpGenerator_LeaveContext'), c.ExprList(c.ID(self.gen_inst.name))))
		super()._runner_cleanup()

	def _runner_leave(self):
		'''In order to leave a coroutine, we set the return context to NULL and transfer back.  The generator will
			raise a StopError in the owning context for us.'''
		self.v.ctx.add(c.Assignment('=', c.ArrayRef(c.ID(self.args_name), c.Constant('integer', self.RETURN_INDEX)), c.ID('NULL')))
		self.v.ctx.add(c.FuncCall(c.ID('MpGenerator_Yield'), c.ExprList(c.ID(self.gen_inst.name))))


	def do_yield(self, rv_inst):
		# assign to our yielded slot slot
		if not rv_inst:
			rv_inst = self.v.none

		# set yielded slot: tp_iter is responsible for incref, the caller of PyIter_Next is responsible for decref
		ret_ref = c.ArrayRef(c.ID(self.args_name), c.Constant('integer', self.RETURN_INDEX))

		self.v.ctx.add(c.Assignment('=', ret_ref, c.ID(rv_inst.name)))

		with self.v.scope.ll.maybe_recursive_call():
			# transfer control back to originator
			self.v.ctx.add(c.FuncCall(c.ID('MpGenerator_LeaveContext'), c.ExprList(c.ID(self.gen_inst.name))))
			self.v.ctx.add(c.FuncCall(c.ID('MpGenerator_Yield'), c.ExprList(c.ID(self.gen_inst.name))))
			self.v.ctx.add(c.FuncCall(c.ID('MpGenerator_EnterContext'), c.ExprList(c.ID(self.gen_inst.name))))

		# check for dealloc and jump to cleanup
		if_exhausted = self.v.ctx.add(c.If(
				c.ArrayRef(c.ID(self.args_name), c.Constant('integer', self.SEND_INDEX)),
					c.Compound(), None))
		with self.v.new_context(if_exhausted.iftrue):
			self.v.ctx.add(c.Goto('end'))


