'''
Copyright (c) 2011, Terrence Cole.
All rights reserved.
'''
from contextlib import contextmanager
from melano.c import ast as c
from melano.c.types.integer import CIntegerLL
from melano.c.types.pydict import PyDictLL
from melano.c.types.pyinteger import PyIntegerLL
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
		self.args_pos_map = [] # map position to c level names

		# the ll name and instance representing the c function that does arg decoding for python style calls
		self.c_pystub_func = None

		# the ll name and instance representing the c function that runs the python function
		self.c_runner_func = None

		# the ll name and instance representing the py callable function object
		self.c_obj = None

		# args to the stub functions
		self.stub_self_inst = None
		self.stub_args_tuple = None
		self.stub_kwargs_dict = None
		self.stub_arg_insts = []


	def prepare(self):
		pass


	def attach_defaults(self, ctx, default_insts, kwdefault_insts):
		if default_insts:
			tmp = PyTupleLL(None, self.visitor)
			tmp.declare(self.visitor.scope.context, name=self.hlnode.owner.name + "_defaults")
			tmp.pack(ctx, *default_insts)
			self.c_obj.set_attr_string(ctx, '__defaults__', tmp)
		if kwdefault_insts:
			tmp = PyDictLL(None, self.visitor)
			tmp.declare(self.visitor.scope.context, name=self.hlnode.owner.name + "_kwdefaults")
			tmp.new(ctx)
			for name, inst in kwdefault_insts:
				tmp.set_item_string(ctx, name, inst)
			self.c_obj.set_attr_string(ctx, '__kwdefaults__', tmp)


	def attach_annotations(self, ctx, ret, args, vararg_name, vararg, kwonlyargs, kwarg_name, kwarg):
		if not (ret or args or vararg or kwonlyargs or kwarg):
			return

		ctx.add(c.Comment("build annotations dict"))
		tmp = PyDictLL(None, self.visitor)
		tmp.declare(self.visitor.scope.context, name=self.hlnode.owner.name + '_annotations')
		tmp.new(ctx)

		if ret:
			tmp.set_item_string(ctx, 'return', ret)
		if vararg:
			tmp.set_item_string(ctx, vararg_name, vararg)
		if kwarg:
			tmp.set_item_string(ctx, kwarg_name, kwarg)
		for name, ann in args:
			if ann:
				tmp.set_item_string(ctx, str(name), ann)
		for name, ann in kwonlyargs:
			if ann:
				tmp.set_item_string(ctx, str(name), ann)

		self.c_obj.set_attr_string(ctx, '__annotations__', tmp)



	### MelanoFunction
	def declare_function_object(self, ctx, tu, docstring):
		# create the function definition structure
		c_name = c.Constant('string', PyStringLL.str2c(self.hlnode.owner.name))
		c_docstring = c.Constant('string', PyStringLL.str2c(docstring)) if docstring else c.ID('NULL')

		# create the function pyobject itself
		self.c_obj = PyObjectLL(self.hlnode, self.visitor)
		self.c_obj.declare(tu, ['static'], name=self.hlnode.owner.global_c_name + "_pycfunc")
		ctx.add(c.Assignment('=', c.ID(self.c_obj.name), c.FuncCall(c.ID('PyMelanoFunction_New'), c.ExprList(
													c_name, c.ID(self.c_pystub_func.decl.name), c_docstring))))
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
		name = tu.reserve_name(self.hlnode.owner.global_c_name + '_pystub')
		self.c_pystub_func = c.FuncDef(
			c.Decl(name,
				c.FuncDecl(param_list,
						c.PtrDecl(c.TypeDecl(name, c.IdentifierType('PyObject')))), quals=['static']),
			c.Compound()
		)
		tu.add_fwddecl(self.c_pystub_func.decl)
		tu.add(self.c_pystub_func)

	def stub_intro(self, ctx):
		ctx.reserve_name('self')
		self.stub_self_inst = PyObjectLL(None, self.visitor)
		self.stub_self_inst.name = 'self'
		ctx.reserve_name('args')
		self.stub_args_tuple = PyTupleLL(None, self.visitor)
		self.stub_args_tuple.name = 'args'
		ctx.reserve_name('kwargs')
		self.stub_kwargs_dict = PyDictLL(None, self.visitor)
		self.stub_kwargs_dict.name = 'kwargs'
		ctx.add_variable(c.Decl('__return_value__', c.PtrDecl(c.TypeDecl('__return_value__', c.IdentifierType('PyObject'))), init=c.ID('NULL')), False)

	def stub_load_args(self, ctx, args, defaults, vararg, kwonlyargs, kw_defaults, kwarg):
		#TODO: this is really ugly -- makes extensive use of self.visitor; we really need a better way to expose
		#		py2c functionality here without just passing a reference to every user

		self.stub_arg_insts = []

		# get args ref
		args_tuple = self.stub_args_tuple
		kwargs_dict = self.stub_kwargs_dict

		# get copy of kwargs -- clear items out of it as we load them, or skip entirely
		kwargs_inst = kwargs_dict.copy(ctx) if kwarg else None

		# load positional and normal keyword args
		if args:
			c_args_size = CIntegerLL(None, self.visitor)
			c_args_size.declare(self.visitor.scope.context, name='args_size')
			args_tuple.get_size_unchecked(ctx, c_args_size)

			arg_insts = [None] * len(args)
			for i, arg in enumerate(args):
				# Note: different scope than the actual args are declared in.. need to stub them out here
				#TODO: make this type pull from the arg.arg.hl.get_type() through lookup... maybe create dup_ll_type or something
				arg_insts[i] = PyObjectLL(arg.arg.hl, self.visitor)
				arg_insts[i].declare(self.visitor.scope.context)

				# query if in positional args
				ctx.add(c.Comment("Grab arg {}".format(str(arg.arg))))
				query_inst = c.If(c.BinaryOp('>', c.ID(c_args_size.name), c.Constant('integer', i)), c.Compound(), c.Compound())
				ctx.add(query_inst)

				## get the positional arg on the true side
				args_tuple.get_unchecked(query_inst.iftrue, i, arg_insts[i])

				## get the keyword arg on the false side
				have_kwarg = query_inst.iffalse.add(c.If(c.ID('kwargs'), c.Compound(), None))

				### if we took kwargs, then get it directly
				kwargs_dict.get_item_string_nofail(have_kwarg.iftrue, str(arg.arg), arg_insts[i])

				### if no kwargs passed or the item was not in the kwargs, load the default from defaults
				query_default_inst = query_inst.iffalse.add(c.If(c.UnaryOp('!', c.ID(arg_insts[i].name)), c.Compound(), c.Compound()))
				with self.visitor.new_context(query_default_inst.iftrue):
					kwstartoffset = len(args) - len(defaults)
					if i >= kwstartoffset:
						# try loading from defaults
						default_offset = i - kwstartoffset
						tmp = PyTupleLL(None, self.visitor)
						tmp.declare(self.visitor.scope.context)
						query_default_inst.iftrue.add(c.Assignment('=', c.ID(tmp.name),
								c.FuncCall(c.ID('PyObject_GetAttrString'), c.ExprList(c.ID(self.c_obj.name), c.Constant('string', '__defaults__')))))
						query_default_inst.iftrue.add(c.Assignment('=', c.ID(arg_insts[i].name),
								c.FuncCall(c.ID('PyTuple_GetItem'), c.ExprList(c.ID(tmp.name), c.Constant('integer', default_offset)))))
						query_default_inst.iftrue.add(c.FuncCall(c.ID('Py_INCREF'), c.ID(arg_insts[i].name)))
					else:
						# emit an error for an unpassed arg
						with self.visitor.new_context(query_default_inst.iftrue):
							self.fail('PyExc_TypeError', 'Missing arg {}'.format(str(arg)))

				# if we did get the item out of the kwargs, delete it from the inst copy so it's not duped in the args we pass 
				with self.visitor.new_context(query_default_inst.iffalse):
					if kwargs_inst:
						kwargs_inst.del_item_string(self.visitor.context, str(arg.arg))
			self.stub_arg_insts.extend(arg_insts)

		# add unused args to varargs and pass if in taken args or error if not
		if vararg:
			ctx.add(c.Comment('load varargs'))
			vararg_inst = args_tuple.get_slice(ctx, len(args), args_tuple.get_length(ctx))
			self.stub_arg_insts.append(vararg_inst)
		else:
			len_inst = args_tuple.get_length(ctx)
			ifstmt = ctx.add(c.If(c.BinaryOp('>', c.ID(len_inst.name), c.Constant('integer', len(args))), c.Compound(), None))
			with self.visitor.new_context(ifstmt.iftrue):
				self.fail_formatted('PyExc_TypeError', "{}() takes exactly {} positional arguments (%d given)".format(self.hlnode.owner.name, len(args)), len_inst)

		# load all keyword only args
		if kwonlyargs:
			kwarg_insts = [None] * len(kwonlyargs)
			for i, arg in enumerate(kwonlyargs):
				kwarg_insts[i] = PyObjectLL(arg.arg.hl, self.visitor)
				kwarg_insts[i].declare(self.visitor.scope.context)

			# ensure we have kwargs at all
			have_kwarg = c.If(c.ID('kwargs'), c.Compound(), c.Compound())
			ctx.add(have_kwarg)

			## in have_kwarg.iftrue, load all kwargs from the kwargs dict
			for i, arg in enumerate(kwonlyargs):
				kwargs_dict.get_item_string_nofail(have_kwarg.iftrue, str(arg.arg), kwarg_insts[i])
				need_default = have_kwarg.iftrue.add(c.If(c.UnaryOp('!', c.ID(kwarg_insts[i].name)), c.Compound(), c.Compound()))

				### not found in kwdict, means we need to load from default
				with self.visitor.new_context(need_default.iftrue):
					tmp = PyDictLL(None, self.visitor)
					tmp.declare(self.visitor.scope.context)
					need_default.iftrue.add(c.Assignment('=', c.ID(tmp.name),
						c.FuncCall(c.ID('PyObject_GetAttrString'), c.ExprList(c.ID(self.c_obj.name), c.Constant('string', '__kwdefaults__')))))
					need_default.iftrue.add(c.Assignment('=', c.ID(kwarg_insts[i].name),
						c.FuncCall(c.ID('PyDict_GetItemString'), c.ExprList(c.ID(tmp.name), c.Constant('string', str(arg.arg))))))
					self.fail_if_null(need_default.iftrue, kwarg_insts[i].name)
				### found in kwdict, means we need to delete from kwdict to avoid passing duplicate arg in kwargs
				with self.visitor.new_context(need_default.iffalse):
					if kwargs_inst:
						kwargs_inst.del_item_string(self.visitor.context, str(arg.arg))


			## if have_kwarg.iffalse, just load from the kwargs dict
			for i, arg in enumerate(kwonlyargs):
				tmp = PyDictLL(None, self.visitor)
				tmp.declare(self.visitor.scope.context)
				have_kwarg.iffalse.add(c.Assignment('=', c.ID(tmp.name),
					c.FuncCall(c.ID('PyObject_GetAttrString'), c.ExprList(c.ID(self.c_obj.name), c.Constant('string', '__kwdefaults__')))))
				have_kwarg.iffalse.add(c.Assignment('=', c.ID(kwarg_insts[i].name),
					c.FuncCall(c.ID('PyDict_GetItemString'), c.ExprList(c.ID(tmp.name), c.Constant('string', str(arg.arg))))))
				self.fail_if_null(have_kwarg.iffalse, kwarg_insts[i].name)
			self.stub_arg_insts.extend(kwarg_insts)

		# pass remainder of kwargs dict in as the kwarg slot
		if kwarg:
			self.stub_arg_insts.append(kwargs_inst)
		'''
		# if we have items left in the kwargs dict:
		#		- if we don't take a kwargs slot, then raise a TypeError
		#		- if the args would have overrided an argument we took, then raise a TypeError
		#import pdb; pdb.set_trace()
		if kwargs_dict:
			ifkwargs = self.visitor.context.add(c.If(c.ID(kwargs_dict.name), c.Compound(), None))
			with self.visitor.new_context(ifkwargs.iftrue):
				tmp = kwargs_dict.mapping_size(self.visitor.context)
				have_extra = self.visitor.context.add(c.If(c.BinaryOp('<', c.Constant('integer', 0), c.ID(tmp.name)), c.Compound(), None))
				with self.visitor.new_context(have_extra.iftrue):
					if not kwarg:
						#tmp = kwargs_dict.mapping_keys(self.visitor.context)
						#key = CIntegerLL(None, self.visitor)
						#key.declare(self.visitor.scope.context, name='_key')
						#key.set_constant(self.visitor.context, 0)
						#first_extra_inst = tmp.sequence_get_item(self.visitor.context, key)
						#first_extra_inst = first_extra_inst.str(self.visitor.context)
						#first_extra_inst = first_extra_inst.as_c_string(self.visitor.context)
						self.fail('PyExc_TypeError', self.hlnode.owner.name + "() got an unexpected keyword argument '%s'")
				#out: foo() got an unexpected keyword argument 'e'
				#out: foo() got multiple values for keyword argument 'a'
		'''


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
		if vararg: out.extend([c.ID(vararg.hl.ll.name)])
		out.extend([c.ID(arg.arg.hl.ll.name) for arg in kwonlyargs])
		if kwarg: out.extend([c.ID(kwarg.hl.ll.name)])
		return out


	def transfer_to_runnerfunc(self, ctx, args, vararg, kwonlyargs, kwarg):
		#args = self._buildargs_idlist(args, vararg, kwonlyargs, kwarg)
		args = [c.ID(inst.name) for inst in self.stub_arg_insts]
		ctx.add(c.Assignment('=', c.ID('__return_value__'), c.FuncCall(c.ID(self.c_runner_func.decl.name),
																	c.ExprList(c.ID('self'), *args))))


	def stub_outro(self, ctx):
		ctx.add(c.Label('end'))
		for name in reversed(ctx.cleanup):
			ctx.add(c.FuncCall(c.ID('Py_XDECREF'), c.ExprList(c.ID(name))))
		ctx.add(c.Return(c.ID('__return_value__')))



	# Runner
	def create_runnerfunc(self, tu, args, vararg, kwonlyargs, kwarg):
		body = c.Compound()
		body.visitor = self.visitor

		base_decl = c.Decl('__self__', c.PtrDecl(c.TypeDecl('__self__', c.IdentifierType('PyObject'))))

		arg_decls = []
		for arg in args:
			ll_inst = self.visitor.create_ll_instance(arg.arg.hl)
			ll_inst.name = body.reserve_name(str(arg.arg))
			arg_decls.append(c.Decl(ll_inst.name, c.PtrDecl(c.TypeDecl(ll_inst.name, c.IdentifierType('PyObject')))))
		if vararg:
			ll_inst = self.visitor.create_ll_instance(vararg.hl)
			ll_inst.name = body.reserve_name(str(vararg))
			arg_decls.append(c.Decl(ll_inst.name, c.PtrDecl(c.TypeDecl(ll_inst.name, c.IdentifierType('PyObject')))))

		kw_decls = []
		for arg in kwonlyargs:
			ll_inst = self.visitor.create_ll_instance(arg.arg.hl)
			ll_inst.name = body.reserve_name(str(arg.arg))
			kw_decls.append(c.Decl(ll_inst.name, c.PtrDecl(c.TypeDecl(ll_inst.name, c.IdentifierType('PyObject')))))
		if kwarg:
			ll_inst = self.visitor.create_ll_instance(kwarg.hl)
			ll_inst.name = body.reserve_name(str(kwarg))
			kw_decls.append(c.Decl(ll_inst.name, c.PtrDecl(c.TypeDecl(ll_inst.name, c.IdentifierType('PyObject')))))

		param_list = c.ParamList(base_decl, *(arg_decls + kw_decls))
		self._create_runner_common(tu, param_list, PyObjectLL.typedecl(), body)


	def _create_runner_common(self, tu, param_list, return_ty, body):
		name = tu.reserve_name(self.hlnode.owner.global_c_name + '_runner')
		self.c_runner_func = c.FuncDef(
			c.Decl(name, c.FuncDecl(param_list, return_ty), quals=['static']),
			body
		)
		tu.add_fwddecl(self.c_runner_func.decl)
		tu.add(self.c_runner_func)


	def runner_load_args(self, ctx, args, vararg, kwonlyargs, kwarg):
		# load args from parameter list into the locals
		for arg in args:
			#arg_inst = self.visitor.create_ll_instance(arg.arg.hl)
			#arg_inst.name = str(arg.arg)
			arg_inst = arg.arg.hl.ll
			self.locals_map[str(arg.arg)] = arg_inst.name
			self.args_pos_map.append(str(arg.arg))
		if vararg:
			arg_inst = vararg.hl.ll
			self.locals_map[str(vararg)] = arg_inst.name
			self.args_pos_map.append(str(vararg))
		for arg in kwonlyargs:
			#arg_inst = self.visitor.create_ll_instance(arg.arg.hl)
			#arg_inst.name = str(arg.arg)
			arg_inst = arg.arg.hl.ll
			self.locals_map[str(arg.arg)] = arg_inst.name
			self.args_pos_map.append(str(arg.arg))
		if kwarg:
			arg_inst = kwarg.hl.ll
			self.locals_map[str(kwarg)] = arg_inst.name
			self.args_pos_map.append(str(kwarg))


	def runner_load_locals(self, ctx):
		for name, sym in self.hlnode.symbols.items():
			#if name not in self.locals_map and isinstance(sym, Name):
			if name not in self.locals_map and sym.parent.ll is self:
				arg_inst = self.visitor.create_ll_instance(sym)
				arg_inst.declare(self.visitor.scope.context)
				self.locals_map[name] = arg_inst.name


	def get_self_accessor(self):
		'''For use by "super" so we can find ourself automaticlaly when called without args'''
		return c.ID(self.args_pos_map[0])


	def runner_intro(self, ctx):
		ctx.add_variable(c.Decl('__return_value__', c.PtrDecl(c.TypeDecl('__return_value__', c.IdentifierType('PyObject'))), init=c.ID('NULL')), False)


	def runner_outro(self, ctx):
		ctx.add(c.Assignment('=', c.ID('__return_value__'), c.ID(self.visitor.none.name)))
		ctx.add(c.Label('end'))
		for name in reversed(ctx.cleanup):
			ctx.add(c.FuncCall(c.ID('Py_XDECREF'), c.ExprList(c.ID(name))))
		ctx.add(c.Return(c.ID('__return_value__')))


	def del_attr_string(self, ctx, attrname):
		ctx.add(c.FuncCall(c.ID('Py_XDECREF'), c.ExprList(c.ID(self.locals_map[attrname]))))
		ctx.add(c.Assignment('=', c.ID(self.locals_map[attrname]), c.ID('NULL')))


	def set_attr_string(self, ctx, attrname, val):
		ctx.add(c.FuncCall(c.ID('Py_XDECREF'), c.ExprList(c.ID(self.locals_map[attrname]))))
		ctx.add(c.FuncCall(c.ID('Py_INCREF'), c.ExprList(c.ID(val.name))))
		ctx.add(c.Assignment('=', c.ID(self.locals_map[attrname]), c.ID(val.name)))


	def get_attr_string(self, ctx, attrname, outvar):
		ctx.add(c.Assignment('=', c.ID(outvar.name), c.ID(self.locals_map[attrname])))
		self.except_if_null(ctx, outvar.name, 'PyExc_UnboundLocalError', "local variable '{}' referenced before assignment".format(attrname))
		outvar.incref(ctx)


	@contextmanager
	def maybe_recursive_call(self, ctx):
		yield
