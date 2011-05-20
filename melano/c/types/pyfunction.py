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


	def attach_defaults(self, default_insts, kwdefault_insts):
		if default_insts:
			tmp = PyTupleLL(None, self.v)
			tmp.declare_tmp(name=self.hlnode.owner.name + "_defaults")
			tmp.pack(*default_insts)
			self.c_obj.set_attr_string('__defaults__', tmp)
			tmp.decref()
		if kwdefault_insts:
			tmp = PyDictLL(None, self.v)
			tmp.declare_tmp(name=self.hlnode.owner.name + "_kwdefaults")
			tmp.new()
			for name, inst in kwdefault_insts:
				if inst is None:
					self.v.none.incref()
					tmp.set_item_string(name, self.v.none)
				else:
					tmp.set_item_string(name, inst)
					inst.decref()
			self.c_obj.set_attr_string('__kwdefaults__', tmp)
			tmp.decref()


	def attach_annotations(self, ret, args, vararg_name, vararg, kwonlyargs, kwarg_name, kwarg):
		if not (ret or args or vararg or kwonlyargs or kwarg):
			return

		self.v.ctx.add(c.Comment("build annotations dict"))
		tmp = PyDictLL(None, self.v)
		tmp.declare_tmp(name=self.hlnode.owner.name + '_annotations')
		tmp.new()

		if ret:
			tmp.set_item_string('return', ret)
		if vararg:
			tmp.set_item_string(vararg_name, vararg)
		if kwarg:
			tmp.set_item_string(kwarg_name, kwarg)
		for name, ann in args:
			if ann:
				tmp.set_item_string(str(name), ann)
		for name, ann in kwonlyargs:
			if ann:
				tmp.set_item_string(str(name), ann)

		self.c_obj.set_attr_string('__annotations__', tmp)
		tmp.decref()



	### MpFunction
	def declare_function_object(self, docstring):
		# create the function definition structure
		c_name = c.Constant('string', PyStringLL.name_to_c_string(self.hlnode.owner.name))
		c_docstring = c.Constant('string', PyStringLL.python_to_c_string(docstring)) if docstring else c.ID('NULL')

		# create the function pyobject itself
		self.c_obj = PyObjectLL(self.hlnode, self.v)
		self.c_obj.declare(is_global=True, quals=['static'], name=self.hlnode.owner.global_c_name + "_pycfunc")
		self.c_obj.xdecref()
		self.v.ctx.add(c.Assignment('=', c.ID(self.c_obj.name), c.FuncCall(c.ID('MpFunction_New'), c.ExprList(
													c_name, c.ID(self.c_pystub_func.decl.name), c_docstring))))
		self.fail_if_null(self.c_obj.name)

		# Note: this incref is for the global reference and needs to get cleaned up too 
		#		-- the inst we return gets owned by the local scope
		self.c_obj.incref()

		return self.c_obj


	### Stub Func
	def create_pystubfunc(self):
		# NOTE: always use kwargs calling convention, because we don't know how external code will call us
		param_list = c.ParamList(
					c.Decl('self', c.PtrDecl(c.TypeDecl('args', c.IdentifierType('PyObject')))),
					c.Decl('args', c.PtrDecl(c.TypeDecl('args', c.IdentifierType('PyObject')))),
					c.Decl('kwargs', c.PtrDecl(c.TypeDecl('kwargs', c.IdentifierType('PyObject')))))

		# create the c function that will correspond to the py function
		name = self.v.tu.reserve_global_name(self.hlnode.owner.global_c_name + '_pystub')
		self.c_pystub_func = c.FuncDef(
			c.Decl(name,
				c.FuncDecl(param_list,
						c.PtrDecl(c.TypeDecl(name, c.IdentifierType('PyObject')))), quals=['static']),
			c.Compound()
		)
		self.v.tu.add_fwddecl(self.c_pystub_func.decl)
		self.v.tu.add(c.WhiteSpace('\n'))
		self.v.tu.add(self.c_pystub_func)

	def stub_intro(self):
		self.stub_self_inst = PyObjectLL(None, self.v)
		self.stub_self_inst.name = self.v.scope.ctx.reserve_name('self', self.v.tu)
		self.stub_args_tuple = PyTupleLL(None, self.v)
		self.stub_args_tuple.name = self.v.scope.ctx.reserve_name('args', self.v.tu)
		self.stub_kwargs_dict = PyDictLL(None, self.v)
		self.stub_kwargs_dict.name = self.v.scope.ctx.reserve_name('kwargs', self.v.tu)
		#FIXME: make this an instance and and inst
		self.v.scope.ctx.add_variable(c.Decl('__return_value__', PyObjectLL.typedecl('__return_value__'), init=c.ID('NULL')), False)

	def stub_load_args(self, args, defaults, vararg, kwonlyargs, kw_defaults, kwarg):
		self.stub_arg_insts = []

		# get args ref
		args_tuple = self.stub_args_tuple
		kwargs_dict = self.stub_kwargs_dict

		# get copy of kwargs -- clear items out of it as we load them, or skip entirely
		if kwarg:
			if_have_kwargs = self.v.ctx.add(c.If(c.ID(kwargs_dict.name), c.Compound(), c.Compound()))
			with self.v.new_context(if_have_kwargs.iftrue):
				kwargs_inst = kwargs_dict.copy()
			with self.v.new_context(if_have_kwargs.iffalse):
				kwargs_dict.new()
				kwargs_inst = kwargs_dict
		else:
			kwargs_inst = None

		# load positional and normal keyword args
		if args:
			c_args_size = CIntegerLL(None, self.v)
			c_args_size.declare_tmp(name='_args_size')
			args_tuple.get_size_unchecked(c_args_size)

			arg_insts = [None] * len(args)
			for i, arg in enumerate(args):
				# Note: different scope than the actual args are declared in.. need to stub them out here
				#TODO: make this type pull from the arg.arg.hl.get_type() through lookup... maybe create dup_ll_type or something
				arg_insts[i] = PyObjectLL(arg.arg.hl, self.v)
				arg_insts[i].declare()

				# query if in positional args
				self.v.ctx.add(c.Comment("Grab arg {}".format(str(arg.arg))))
				query_inst = self.v.ctx.add(c.If(c.BinaryOp('>', c.ID(c_args_size.name), c.Constant('integer', i)), c.Compound(), c.Compound()))

				## get the positional arg on the true side
				with self.v.new_context(query_inst.iftrue):
					args_tuple.get_unchecked(i, arg_insts[i])

				## get the keyword arg on the false side
				with self.v.new_context(query_inst.iffalse):
					have_kwarg = self.v.ctx.add(c.If(c.ID('kwargs'), c.Compound(), None))

					### if we took kwargs, then get it directly
					with self.v.new_context(have_kwarg.iftrue):
						kwargs_dict.get_item_string_nofail(str(arg.arg), arg_insts[i])

					### if no kwargs passed or the item was not in the kwargs, load the default from defaults
					query_default_inst = self.v.ctx.add(c.If(c.UnaryOp('!', c.ID(arg_insts[i].name)), c.Compound(), c.Compound()))
					with self.v.new_context(query_default_inst.iftrue):
						kwstartoffset = len(args) - len(defaults)
						if i >= kwstartoffset:
							# try loading from defaults
							default_offset = i - kwstartoffset
							tmp = PyTupleLL(None, self.v)
							tmp.declare_tmp()
							self.c_obj.get_attr_string('__defaults__', tmp)
							#self.v.ctx.add(c.Assignment('=', c.ID(tmp.name),
							#		c.FuncCall(c.ID('PyObject_GetAttrString'), c.ExprList(c.ID(self.c_obj.name), c.Constant('string', '__defaults__')))))
							#
							tmp.get_unchecked(default_offset, arg_insts[i])
							#self.v.ctx.add(c.Assignment('=', c.ID(arg_insts[i].name),
							#		c.FuncCall(c.ID('PyTuple_GetItem'), c.ExprList(c.ID(tmp.name), c.Constant('integer', default_offset)))))
							arg_insts[i].incref()
							tmp.decref()
							#self.v.ctx.add(c.FuncCall(c.ID('Py_INCREF'), c.ID(arg_insts[i].name)))
						else:
							# emit an error for an unpassed arg
							with self.v.new_context(query_default_inst.iftrue):
								self.fail('PyExc_TypeError', 'Missing arg {}'.format(str(arg)))

					### if we did get the item out of the kwargs, delete it from the inst copy so it's not duped in the args we pass 
					with self.v.new_context(query_default_inst.iffalse):
						if kwargs_inst:
							kwargs_inst.del_item_string(str(arg.arg))
			self.stub_arg_insts.extend(arg_insts)

		# add unused args to varargs and pass if in taken args or error if not
		if vararg:
			self.v.ctx.add(c.Comment('load varargs'))
			vararg_inst = args_tuple.get_slice(len(args), args_tuple.get_length())
			self.stub_arg_insts.append(vararg_inst)
		else:
			len_inst = args_tuple.get_length()
			ifstmt = self.v.ctx.add(c.If(c.BinaryOp('>', c.ID(len_inst.name), c.Constant('integer', len(args))), c.Compound(), None))
			with self.v.new_context(ifstmt.iftrue):
				self.fail_formatted('PyExc_TypeError', "{}() takes exactly {} positional arguments (%d given)".format(self.hlnode.owner.name, len(args)), len_inst)

		# load all keyword only args
		if kwonlyargs:
			kwarg_insts = [None] * len(kwonlyargs)
			for i, arg in enumerate(kwonlyargs):
				kwarg_insts[i] = PyObjectLL(arg.arg.hl, self.v)
				kwarg_insts[i].declare()

			# ensure we have kwargs at all
			have_kwarg = self.v.ctx.add(c.If(c.ID('kwargs'), c.Compound(), c.Compound()))

			## in have_kwarg.iftrue, load all kwargs from the kwargs dict
			with self.v.new_context(have_kwarg.iftrue):
				for i, arg in enumerate(kwonlyargs):
					#FIXME: we can make this significantly more efficient with a bit of work
					kwargs_dict.get_item_string_nofail(str(arg.arg), kwarg_insts[i])
					need_default = self.v.ctx.add(c.If(c.UnaryOp('!', c.ID(kwarg_insts[i].name)), c.Compound(), None))

					### not found in kwdict, means we need to load from default
					with self.v.new_context(need_default.iftrue):
						kwdefaults0 = PyDictLL(None, self.v)
						kwdefaults0.declare_tmp(name='_kwdefaults')
						self.c_obj.get_attr_string('__kwdefaults__', kwdefaults0)
						kwdefaults0.get_item_string(str(arg.arg), kwarg_insts[i])
						kwdefaults0.decref()
					### found in kwdict, means we need to delete from kwdict to avoid passing duplicate arg in kwargs
					if kwargs_inst:
						need_default.iffalse = c.Compound()
						with self.v.new_context(need_default.iffalse):
							kwargs_inst.del_item_string(str(arg.arg))

			## if have_kwarg.iffalse, need to load from the kwdefaults dict
			#TODO: this is identical to the failure case from above
			with self.v.new_context(have_kwarg.iffalse):
				kwdefaults1 = PyDictLL(None, self.v)
				kwdefaults1.declare_tmp(name='_kwdefaults')
				self.c_obj.get_attr_string('__kwdefaults__', kwdefaults1)
				for i, arg in enumerate(kwonlyargs):
					#have_kwarg.iffalse.add(c.Assignment('=', c.ID(kwdefaults1.name),
					#	c.FuncCall(c.ID('PyObject_GetAttrString'), c.ExprList(c.ID(self.c_obj.name), c.Constant('string', '__kwdefaults__')))))
					kwdefaults1.get_item_string(str(arg.arg), kwarg_insts[i])
					#have_kwarg.iffalse.add(c.Assignment('=', c.ID(kwarg_insts[i].name),
					#	c.FuncCall(c.ID('PyDict_GetItemString'), c.ExprList(c.ID(kwdefaults1.name), c.Constant('string', str(arg.arg))))))
					#self.fail_if_null(kwarg_insts[i].name)
				kwdefaults1.decref()

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
			ifkwargs = self.v.context.add(c.If(c.ID(kwargs_dict.name), c.Compound(), None))
			with self.v.new_context(ifkwargs.iftrue):
				tmp = kwargs_dict.mapping_size(self.v.context)
				have_extra = self.v.context.add(c.If(c.BinaryOp('<', c.Constant('integer', 0), c.ID(tmp.name)), c.Compound(), None))
				with self.v.new_context(have_extra.iftrue):
					if not kwarg:
						#tmp = kwargs_dict.mapping_keys(self.v.context)
						#key = CIntegerLL(None, self.v)
						#key.declare(self.v.scope.context, name='_key')
						#key.set_constant(self.v.context, 0)
						#first_extra_inst = tmp.sequence_get_item(self.v.context, key)
						#first_extra_inst = first_extra_inst.str(self.v.context)
						#first_extra_inst = first_extra_inst.as_c_string(self.v.context)
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


	def transfer_to_runnerfunc(self, args, vararg, kwonlyargs, kwarg):
		args = [c.ID(inst.name) for inst in self.stub_arg_insts]
		self.v.ctx.add(c.Assignment('=', c.ID('__return_value__'), c.FuncCall(c.ID(self.c_runner_func.decl.name),
																	c.ExprList(c.ID('self'), *args))))


	def stub_outro(self):
		self.v.ctx.add(c.Label('end'))
		for name in reversed(self.v.ctx.cleanup):
			self.v.ctx.add(c.FuncCall(c.ID('Py_XDECREF'), c.ExprList(c.ID(name))))
		self.v.ctx.add(c.Return(c.ID('__return_value__')))



	# Runner
	def create_runnerfunc(self, args, vararg, kwonlyargs, kwarg):
		body = c.Compound()

		base_decl = c.Decl('__self__', c.PtrDecl(c.TypeDecl('__self__', c.IdentifierType('PyObject'))))

		arg_decls = []
		for arg in args:
			ll_inst = self.v.create_ll_instance(arg.arg.hl)
			ll_inst.name = body.reserve_name(str(arg.arg), self.v.tu)
			arg_decls.append(c.Decl(ll_inst.name, c.PtrDecl(c.TypeDecl(ll_inst.name, c.IdentifierType('PyObject')))))
		if vararg:
			ll_inst = self.v.create_ll_instance(vararg.hl)
			ll_inst.name = body.reserve_name(str(vararg), self.v.tu)
			arg_decls.append(c.Decl(ll_inst.name, c.PtrDecl(c.TypeDecl(ll_inst.name, c.IdentifierType('PyObject')))))

		kw_decls = []
		for arg in kwonlyargs:
			ll_inst = self.v.create_ll_instance(arg.arg.hl)
			ll_inst.name = body.reserve_name(str(arg.arg), self.v.tu)
			kw_decls.append(c.Decl(ll_inst.name, c.PtrDecl(c.TypeDecl(ll_inst.name, c.IdentifierType('PyObject')))))
		if kwarg:
			ll_inst = self.v.create_ll_instance(kwarg.hl)
			ll_inst.name = body.reserve_name(str(kwarg), self.v.tu)
			kw_decls.append(c.Decl(ll_inst.name, c.PtrDecl(c.TypeDecl(ll_inst.name, c.IdentifierType('PyObject')))))

		param_list = c.ParamList(base_decl, *(arg_decls + kw_decls))
		self._create_runner_common(param_list, PyObjectLL.typedecl(), body)


	def _create_runner_common(self, param_list, return_ty, body):
		name = self.v.tu.reserve_global_name(self.hlnode.owner.global_c_name + '_runner')
		self.c_runner_func = c.FuncDef(
			c.Decl(name, c.FuncDecl(param_list, return_ty), quals=['static']),
			body
		)
		self.v.tu.add_fwddecl(self.c_runner_func.decl)
		self.v.tu.add(self.c_runner_func)


	def runner_load_args(self, args, vararg, kwonlyargs, kwarg):
		# load args from parameter list into the locals
		for arg in args:
			arg_inst = arg.arg.hl.ll
			self.locals_map[str(arg.arg)] = arg_inst.name
			self.args_pos_map.append(str(arg.arg))
		if vararg:
			arg_inst = vararg.hl.ll
			self.locals_map[str(vararg)] = arg_inst.name
			self.args_pos_map.append(str(vararg))
		for arg in kwonlyargs:
			arg_inst = arg.arg.hl.ll
			self.locals_map[str(arg.arg)] = arg_inst.name
			self.args_pos_map.append(str(arg.arg))
		if kwarg:
			arg_inst = kwarg.hl.ll
			self.locals_map[str(kwarg)] = arg_inst.name
			self.args_pos_map.append(str(kwarg))


	def runner_load_locals(self):
		for name, sym in self.hlnode.symbols.items():
			#if name not in self.locals_map and isinstance(sym, Name):
			if name not in self.locals_map and sym.parent.ll is self:
				arg_inst = self.v.create_ll_instance(sym)
				arg_inst.declare()
				self.locals_map[name] = arg_inst.name


	def get_self_accessor(self):
		'''For use by "super" so we can find ourself automaticlaly when called without args'''
		return c.ID(self.args_pos_map[0])


	def runner_intro(self):
		self.v.ctx.add_variable(c.Decl('__return_value__', PyObjectLL.typedecl('__return_value__'), init=c.ID('NULL')), False)


	def runner_outro(self):
		'''Toplevel interface to runner cleanup and exit, called by high-level users.  Internal overriders of function should
			not override this method, but the lower-level methods instead.'''
		self._runner_end()
		self._runner_cleanup()
		self._runner_leave()

	def _runner_end(self):
		self.v.none.incref()
		self.v.ctx.add(c.Assignment('=', c.ID('__return_value__'), c.ID(self.v.none.name)))
		self.v.ctx.add(c.Label('end'))

	def _runner_cleanup(self):
		for name in reversed(self.v.ctx.cleanup):
			self.v.ctx.add(c.FuncCall(c.ID('Py_XDECREF'), c.ExprList(c.ID(name))))

	def _runner_leave(self):
		self.v.ctx.add(c.Return(c.ID('__return_value__')))


	def del_attr_string(self, attrname):
		#NOTE: we don't own the ref on our args
		if attrname not in self.args_pos_map:
			self.v.ctx.add(c.FuncCall(c.ID('Py_CLEAR'), c.ExprList(c.ID(self.locals_map[attrname]))))
		else:
			self.v.ctx.add(c.Assignment('=', c.ID(self.locals_map[attrname]), c.ID('NULL')))


	def set_attr_string(self, attrname, val):
		self.v.ctx.add(c.FuncCall(c.ID('Py_XDECREF'), c.ExprList(c.ID(self.locals_map[attrname]))))
		val = val.as_pyobject()
		val.incref()
		self.v.ctx.add(c.Assignment('=', c.ID(self.locals_map[attrname]), c.ID(val.name)))


	def get_attr_string(self, attrname, outvar):
		self.v.ctx.add(c.Assignment('=', c.ID(outvar.name), c.ID(self.locals_map[attrname])))
		self.except_if_null(outvar.name, 'PyExc_UnboundLocalError', "local variable '{}' referenced before assignment".format(attrname))
		outvar.incref()


	@contextmanager
	def maybe_recursive_call(self):
		yield


