'''
Copyright (c) 2011, Terrence Cole.
All rights reserved.
'''
from melano.c import ast as c
from melano.c.types.integer import CIntegerLL
from melano.c.types.pydict import PyDictLL
from melano.c.types.pyobject import PyObjectLL
from melano.c.types.pystring import PyStringLL
from melano.c.types.pytuple import PyTupleLL
from melano.hl.class_ import MelanoClass
from melano.hl.name import Name


class PyFunctionLL(PyObjectLL):
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)

		# map python names to c level names for locals
		self.locals_map = {} # {str: str}

		# the c instantce representing the defaults, for fast access (and since we can't store them on __defaults__ in a PyCFunction)
		self.c_defaults_array = None
		self.c_kwdefaults_array = None
		self.c_kwdefaults_map = {}

		# the c instantce representing the annotations, for fast access (and since we can't store them on __defaults__ in a PyCFunction)
		#self.c_annotations_name = None
		#self.c_annotations_dict = None

		# the ll name and instance representing the c function that does arg decoding for python style calls
		self.c_pystub_func = None

		# the ll name and instance representing the c function that runs the python function
		self.c_runner_func = None

		# the ll name and instance representing the py callable function object
		self.c_obj = None


	def create_defaults(self, tu, defaults, kwdefaults):
		if defaults:
			cnt = len(defaults)
			name = tu.reserve_name(self.hlnode.owner.name + '_defaults')
			self.c_defaults_array = c.Decl(name,
										c.ArrayDecl(c.PtrDecl(c.TypeDecl(name, c.IdentifierType('PyObject'))), cnt),
										init=c.ExprList(*(cnt * [c.ID('NULL')])), quals=['static'])
			tu.add_fwddecl(self.c_defaults_array)
		if kwdefaults:
			cnt = len(kwdefaults)
			name = tu.reserve_name(self.hlnode.owner.name + '_kwdefaults')
			self.c_kwdefaults_array = c.Decl(name,
										c.ArrayDecl(c.PtrDecl(c.TypeDecl(name, c.IdentifierType('PyObject'))), cnt),
										init=c.ExprList(*(cnt * [c.ID('NULL')])), quals=['static'])
			tu.add_fwddecl(self.c_kwdefaults_array)


	def attach_defaults(self, ctx, default_insts, kwdefault_insts):
		for i, default_inst in enumerate(default_insts):
			default_inst.incref(ctx)
			ctx.add(c.Assignment('=', c.ArrayRef(c.ID(self.c_defaults_array.name), c.Constant('integer', i)), c.ID(default_inst.name)))
		for i, default_inst in enumerate(kwdefault_insts):
			default_inst.incref(ctx)
			ctx.add(c.Assignment('=', c.ArrayRef(c.ID(self.c_kwdefaults_array.name), c.Constant('integer', i)), c.ID(default_inst.name)))


	### MelanoFunction
	def create_funcdef(self, ctx, tu, docstring):
		ctx.add(c.Comment('Declare Python stub function "{}"'.format(self.hlnode.owner.name)))

		# create the function definition structure
		c_name = c.Constant('string', PyStringLL.str2c(self.hlnode.owner.name))
		c_docstring = c.Constant('string', PyStringLL.str2c(docstring)) if docstring else c.ID('NULL')

		# create the function pyobject itself
		self.c_obj = PyObjectLL(self.hlnode, self.visitor)
		self.c_obj.declare(tu, ['static'], name=self.hlnode.owner.name + "_pycfunc")
		ctx.add(c.Assignment('=', c.ID(self.c_obj.name), c.FuncCall(c.ID('PyMelanoFunction_New'), c.ExprList(
													c_name, c.ID(self.c_pystub_name), c_docstring))))
		self.fail_if_null(ctx, self.c_obj.name)

		return self.c_obj


	### Stub Func
	def create_pystubfunc(self, tu):
		# NOTE: always use kwargs calling convention, because we don't know how external code will call us
		param_list = c.ParamList(
								c.Decl('self', c.PtrDecl(c.TypeDecl('args', c.IdentifierType('PyObject')))),
								c.Decl('args', c.PtrDecl(c.TypeDecl('args', c.IdentifierType('PyObject')))),
								c.Decl('kwargs', c.PtrDecl(c.TypeDecl('kwargs', c.IdentifierType('PyObject')))))

		# create the c function that will correspond to the py function
		self.c_pystub_name = tu.reserve_name(self.hlnode.owner.name + '_pystub')
		self.c_pystub_func = c.FuncDef(
			c.Decl(self.c_pystub_name,
				c.FuncDecl(param_list,
						c.PtrDecl(c.TypeDecl(self.c_pystub_name, c.IdentifierType('PyObject')))), quals=['static']),
			c.Compound()
		)
		tu.add_fwddecl(self.c_pystub_func.decl)
		tu.add(self.c_pystub_func)

	def stub_intro(self, ctx):
		ctx.add_variable(c.Decl('__return_value__', c.PtrDecl(c.TypeDecl('__return_value__', c.IdentifierType('PyObject'))), init=c.ID('NULL')), False)

	def stub_load_args(self, ctx, args, defaults, vararg, kwonlyargs, kw_defaults, kwarg):
		#TODO: this is really ugly -- makes extensive use of ctx.visitor; we really need a better way to expose
		#		py2c functionality here without just passing a reference to every user

		# get args ref
		ctx.reserve_name('args')
		args_tuple = PyTupleLL(None, self.visitor)
		args_tuple.name = 'args'

		ctx.reserve_name('kwargs')
		kwargs_dict = PyDictLL(None, self.visitor)
		kwargs_dict.name = 'kwargs'

		# load positional and normal keyword args
		if args:
			c_args_size = CIntegerLL(None, self.visitor)
			c_args_size.declare(ctx.visitor.scope.context, name='args_size')
			args_tuple.get_size_unchecked(ctx, c_args_size)

			arg_insts = [None] * len(args)
			for i, arg in enumerate(args):
				# declare local variable for arg ref
				arg_insts[i] = ctx.visitor.create_ll_instance(arg.arg.hl)
				arg_insts[i].declare(ctx.visitor.scope.context)

				# query if in positional args
				ctx.add(c.Comment("Grab arg {}".format(str(arg.arg))))
				query_inst = c.If(c.BinaryOp('>', c.ID(c_args_size.name), c.Constant('integer', i)), c.Compound(), c.Compound())
				ctx.add(query_inst)

				## get the positional arg on the true side
				args_tuple.get_unchecked(query_inst.iftrue, i, arg_insts[i])

				## get the keyword arg on the false side
				have_kwarg = c.If(c.ID('kwargs'), c.Compound(), None)
				query_inst.iffalse.add(have_kwarg)

				### if we took kwargs, then get it directly
				kwargs_dict.get_item_string_nofail(have_kwarg.iftrue, str(arg.arg), arg_insts[i])

				### if no kwargs passed or the item was not in the kwargs, load the default from defaults
				query_default_inst = c.If(c.UnaryOp('!', c.ID(arg_insts[i].name)), c.Compound(), None)
				query_inst.iffalse.add(query_default_inst)

				# try loading from defaults
				#TODO: only get the defaults / kwdefaults once
				kwstartoffset = len(args) - len(defaults)
				if i >= kwstartoffset:
					default_offset = i - kwstartoffset
					query_default_inst.iftrue.add(c.Assignment('=', c.ID(arg_insts[i].name),
															c.ArrayRef(c.ID(self.c_defaults_array.name), c.Constant('integer', default_offset))))
					query_default_inst.iftrue.add(c.FuncCall(c.ID('Py_INCREF'), c.ID(arg_insts[i].name)))
				else:
					# emit an error for an unpassed arg
					with self.visitor.new_context(query_default_inst.iftrue):
						self.fail('PyExc_TypeError', 'Missing arg {}'.format(str(arg)))

		# load all keyword only args
		if kwonlyargs:
			kwarg_insts = [None] * len(kwonlyargs)
			for i, arg in enumerate(kwonlyargs):
				kwarg_insts[i] = ctx.visitor.create_ll_instance(arg.arg.hl)
				kwarg_insts[i].declare(ctx.visitor.scope.context)

			# ensure we have kwargs at all
			have_kwarg = c.If(c.ID('kwargs'), c.Compound(), c.Compound())
			ctx.add(have_kwarg)

			## in have_kwarg.iftrue, load all kwargs from the kwargs dict
			for i, arg in enumerate(kwonlyargs):
				kwargs_dict.get_item_string_nofail(have_kwarg.iftrue, str(arg.arg), kwarg_insts[i])
				need_default = c.If(c.UnaryOp('!', c.ID(kwarg_insts[i].name)), c.Compound(), None)
				have_kwarg.iftrue.add(need_default)

				### not found in kwdict, means we need to load from default
				need_default.iftrue.add(c.Assignment('=', c.ID(kwarg_insts[i].name),
													c.ArrayRef(c.ID(self.c_kwdefaults_array.name), c.Constant('integer', i))))

			## if have_kwarg.iffalse, just load from teh kwargs dict
			for i, arg in enumerate(kwonlyargs):
				have_kwarg.iffalse.add(c.Assignment('=', c.ID(kwarg_insts[i].name),
													c.ArrayRef(c.ID(self.c_kwdefaults_array.name), c.Constant('integer', i))))

		#TODO: add unused args to varargs and pass if needed or error if not
		#TODO: add unused kwargs to varargs and pass if needed or error if not

	def _buildargs(self, args, vararg, kwonlyargs, kwarg):
		out = []
		if args: out.extend(args)
		if vararg: out.extend([vararg])
		if kwonlyargs: out.extend(kwonlyargs)
		if kwarg: out.extend([kwarg])
		return out

	def _buildargs_idlist(self, args, vararg, kwonlyargs, kwarg):
		out = []
		out.extend([c.ID(arg.arg.hl.ll.name) for arg in args])
		if vararg: out.extend([c.ID(vararg)])
		out.extend([c.ID(arg.arg.hl.ll.name) for arg in kwonlyargs])
		if kwarg: out.extend([c.ID(kwarg)])
		return out

	def transfer_to_runnerfunc(self, ctx, args, vararg, kwonlyargs, kwarg):
		args = self._buildargs_idlist(args, vararg, kwonlyargs, kwarg)
		ctx.add(c.Assignment('=', c.ID('__return_value__'), c.FuncCall(c.ID(self.c_runner_func.decl.name),
																	c.ExprList(c.ID('self'), *args))))


	def stub_outro(self, ctx):
		ctx.add(c.Label('end'))
		for name in reversed(ctx.cleanup):
			ctx.add(c.FuncCall(c.ID('Py_XDECREF'), c.ExprList(c.ID(name))))
		ctx.add(c.Return(c.ID('__return_value__')))



	# Runner
	def create_runnerfunc(self, tu, args, vararg, kwonlyargs, kwarg):
		base_decl = c.Decl('__self__', c.PtrDecl(c.TypeDecl('__self__', c.IdentifierType('PyObject'))))
		args_decls = [c.Decl(str(arg.arg), c.PtrDecl(c.TypeDecl(str(arg.arg), c.IdentifierType('PyObject')))) for arg in args]
		if vararg:
			args_decls.append(c.Decl(str(vararg), c.PtrDecl(c.TypeDecl(str(vararg), c.IdentifierType('PyObject')))))
		kw_decls = [c.Decl(str(arg.arg), c.PtrDecl(c.TypeDecl(str(arg.arg), c.IdentifierType('PyObject')))) for arg in kwonlyargs]
		if kwarg:
			args_decls.append(c.Decl(str(kwarg), c.PtrDecl(c.TypeDecl(str(kwarg), c.IdentifierType('PyObject')))))
		param_list = c.ParamList(base_decl, *(args_decls + kw_decls))
		self._create_runner_common(tu, param_list, PyObjectLL.typedecl())

	def _create_runner_common(self, tu, param_list, return_ty):
		name = tu.reserve_name(self.hlnode.owner.name + '_runner')
		self.c_runner_func = c.FuncDef(
			c.Decl(name, c.FuncDecl(param_list, return_ty), quals=['static']),
			c.Compound()
		)
		tu.add_fwddecl(self.c_runner_func.decl)
		tu.add(self.c_runner_func)

	def runner_load_args(self, ctx, args, vararg, kwonlyargs, kwarg):
		# load args from parameter list into the locals array
		for arg in args:
			arg_inst = self.visitor.create_ll_instance(arg.arg.hl)
			arg_inst.name = str(arg.arg)
			self.locals_map[str(arg.arg)] = str(arg.arg)
			#self.set_attr_string(ctx, str(arg.arg), arg_inst)
		for arg in kwonlyargs:
			arg_inst = self.visitor.create_ll_instance(arg.arg.hl)
			arg_inst.name = str(arg.arg)
			self.locals_map[str(arg.arg)] = str(arg.arg)
			#self.set_attr_string(ctx, str(arg.arg), arg_inst)

	def runner_load_locals(self, ctx):
		for name, sym in self.hlnode.symbols.items():
			if name not in self.locals_map and isinstance(sym, Name):
				arg_inst = self.visitor.create_ll_instance(sym)
				arg_inst.declare(self.visitor.scope.context)
				self.locals_map[name] = arg_inst.name

	def runner_intro(self, ctx):
		ctx.add_variable(c.Decl('__return_value__', c.PtrDecl(c.TypeDecl('__return_value__', c.IdentifierType('PyObject'))), init=c.ID('NULL')), False)
		ctx.add_variable(c.Decl('__jmp_ctx__', c.PtrDecl(c.TypeDecl('__jmp_ctx__', c.IdentifierType('void'))), init=c.ID('NULL')), False)

	def runner_outro(self, ctx):
		ctx.add(c.Assignment('=', c.ID('__return_value__'), c.ID('None')))
		ctx.add(c.Label('end'))
		for name in reversed(ctx.cleanup):
			ctx.add(c.FuncCall(c.ID('Py_XDECREF'), c.ExprList(c.ID(name))))
		ctx.add(c.Return(c.ID('__return_value__')))


	def set_attr_string(self, ctx, attrname, val):
		ctx.add(c.FuncCall(c.ID('Py_XDECREF'), c.ExprList(c.ID(self.locals_map[attrname]))))
		ctx.add(c.FuncCall(c.ID('Py_INCREF'), c.ExprList(c.ID(val.name))))
		ctx.add(c.Assignment('=', c.ID(self.locals_map[attrname]), c.ID(val.name)))


	def get_attr_string(self, ctx, attrname, outvar):
		ctx.add(c.Assignment('=', c.ID(outvar.name), c.ID(self.locals_map[attrname])))
		outvar.incref(ctx)


