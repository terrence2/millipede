'''
Copyright (c) 2011, Terrence Cole.
All rights reserved.
'''
from melano.c import ast as c
from melano.c.types.pyobject import PyObjectLL
from melano.c.types.pystring import PyStringLL
from melano.hl.class_ import MelanoClass


class PyCFunctionLL(PyObjectLL):
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)

		# the c instance representing the array of local variables
		self.c_locals_name = None
		self.c_locals_array = None

		# the c instantce representing the defaults, for fast access (and since we can't store them on __defaults__ in a PyCFunction)
		self.c_defaults_name = None
		self.c_defaults_array = None

		# the c instantce representing the kwdefaults, for fast access (and since we can't store them on __defaults__ in a PyCFunction)
		self.c_kwdefaults_name = None
		self.c_kwdefaults_array = None
		self.c_kwdefaults_map = {}

		# the c instantce representing the annotations, for fast access (and since we can't store them on __defaults__ in a PyCFunction)
		self.c_annotations_name = None
		self.c_annotations_dict = None

		# the ll name and instance representing the c function that does arg decoding for python style calls
		self.c_pystub_name = None
		self.c_pystub_func = None

		# the ll name and instance representing the c function that runs the python function
		self.c_runner_name = None
		self.c_runner_func = None

		# ethe name of the struct that defines the function
		#self.funcdef_name = None

		# the ll name and instance representing the py callable function object
		self.c_obj = None


	def create_locals(self, tu):
		self.c_locals_name = tu.reserve_name(self.hlnode.owner.name + '_locals')
		cnt = self.hlnode.get_locals_count()
		self.c_locals_array = c.Decl(self.c_locals_name,
									c.ArrayDecl(c.PtrDecl(c.TypeDecl(self.c_locals_name, c.IdentifierType('PyObject'))), cnt),
									init=c.ExprList(*(cnt * [c.ID('NULL')])), quals=['static'])
		tu.add_fwddecl(self.c_locals_array)


	def create_defaults(self, tu, cnt):
		self.c_defaults_name = tu.reserve_name(self.hlnode.owner.name + '_defaults')
		self.c_defaults_array = c.Decl(self.c_defaults_name,
									c.ArrayDecl(c.PtrDecl(c.TypeDecl(self.c_defaults_name, c.IdentifierType('PyObject'))), cnt),
									init=c.ExprList(*(cnt * [c.ID('NULL')])), quals=['static'])
		tu.add_fwddecl(self.c_defaults_array)


	def create_kwdefaults(self, tu, cnt):
		self.c_kwdefaults_name = tu.reserve_name(self.hlnode.owner.name + '_kwdefaults')
		self.c_kwdefaults_array = c.Decl(self.c_kwdefaults_name,
									c.ArrayDecl(c.PtrDecl(c.TypeDecl(self.c_kwdefaults_name, c.IdentifierType('PyObject'))), cnt),
									init=c.ExprList(*(cnt * [c.ID('NULL')])), quals=['static'])
		tu.add_fwddecl(self.c_kwdefaults_array)


	def create_pystubfunc(self, tu):
		# NOTE: always use kwargs calling convention, because we don't know how external code will call us
		param_list = c.ParamList(
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


	def create_runnerfunc(self, tu, args, vararg, kwonlyargs, kwarg):
		args_decls = [c.Decl(str(arg.arg), c.PtrDecl(c.TypeDecl(str(arg.arg), c.IdentifierType('PyObject')))) for arg in args]
		if vararg:
			args_decls.append(c.Decl(str(vararg), c.PtrDecl(c.TypeDecl(str(vararg), c.IdentifierType('PyObject')))))
		kw_decls = [c.Decl(str(arg.arg), c.PtrDecl(c.TypeDecl(str(arg.arg), c.IdentifierType('PyObject')))) for arg in kwonlyargs]
		if kwarg:
			args_decls.append(c.Decl(str(kwarg), c.PtrDecl(c.TypeDecl(str(kwarg), c.IdentifierType('PyObject')))))

		param_list = c.ParamList(*(args_decls + kw_decls))
		self.c_runner_name = tu.reserve_name(self.hlnode.owner.name + '_runner')
		self.c_runner_func = c.FuncDef(
			c.Decl(self.c_runner_name,
				c.FuncDecl(param_list, \
						c.PtrDecl(c.TypeDecl(self.c_runner_name, c.IdentifierType('PyObject')))), quals=['static']),
			c.Compound()
		)
		tu.add_fwddecl(self.c_runner_func.decl)
		tu.add(self.c_runner_func)


	def call_runnerfunc(self, ctx, args, vararg, kwonlyargs, kwarg):
		args = [c.ID(str(arg.arg)) for arg in args]
		kwargs = [c.ID(str(arg.arg)) for arg in kwonlyargs]
		ctx.add(c.Assignment('=', c.ID('__return_value__'), c.FuncCall(c.ID(self.c_runner_name), c.ExprList(*(args + kwargs)))))


	def create_funcdef(self, ctx, tu, docstring):
		ctx.add(c.Comment('Declare Python stub function "{}"'.format(self.hlnode.owner.name)))

		# create the function definition structure
		#self.funcdef_name = ctx.reserve_name(self.hlnode.owner.name + '_def')
		c_name = c.Constant('string', PyStringLL.str2c(self.hlnode.owner.name))
		c_docstring = c.Constant('string', PyStringLL.str2c(docstring)) if docstring else c.ID('NULL')
		#ctx.add_variable(c.Decl(self.funcdef_name, c.TypeDecl(self.funcdef_name, c.Struct('PyMethodDef')),
		#		init=c.ExprList(
		#					c.Constant('string', str(self.hlnode.owner.name)),
		#					c.Cast(c.IdentifierType('PyCFunction'), c.ID(self.c_pystub_name)),
		#					c.BinaryOp('|', c.ID('METH_VARARGS'), c.ID('METH_KEYWORDS')), c_docstring)), False)

		# create the function pyobject itself
		self.c_obj = PyObjectLL(self.hlnode)
		self.c_obj.declare(tu, ['static'], name=self.hlnode.owner.name + "_pycfunc")
		ctx.add(c.Assignment('=', c.ID(self.c_obj.name), c.FuncCall(c.ID('PyMelanoFunction_New'), c.ExprList(
													c_name, c.ID(self.c_pystub_name), c_docstring))))
		self.fail_if_null(ctx, self.c_obj.name)

		return self.c_obj


	def set_attr_string(self, ctx, attrname, val):
		attroffset = self.hlnode.locals_map[attrname]
		ctx.add(c.FuncCall(c.ID('Py_INCREF'), c.ExprList(c.ID(val.name))))
		ctx.add(c.Assignment('=', c.ArrayRef(self.c_locals_name, attroffset), c.ID(val.name)))

		# TODO: also assign to a local?


	def get_attr_string(self, ctx, attrname, outvar):
		attroffset = self.hlnode.locals_map[attrname]
		ctx.add(c.Assignment('=', c.ID(outvar.name), c.ArrayRef(self.c_locals_name, attroffset)))

		#TODO: use a local?


	def stub_intro(self, ctx):
		ctx.add_variable(c.Decl('__return_value__', c.PtrDecl(c.TypeDecl('__return_value__', c.IdentifierType('PyObject'))), init=c.ID('NULL')), False)


	def stub_outro(self, ctx):
		ctx.add(c.Label('end'))
		for name in reversed(ctx.cleanup):
			ctx.add(c.FuncCall(c.ID('Py_XDECREF'), c.ExprList(c.ID(name))))
		ctx.add(c.Return(c.ID('__return_value__')))


	def runner_intro(self, ctx):
		ctx.add_variable(c.Decl('__return_value__', c.PtrDecl(c.TypeDecl('__return_value__', c.IdentifierType('PyObject'))), init=c.ID('NULL')), False)


	def runner_outro(self, ctx):
		ctx.add(c.Assignment('=', c.ID('__return_value__'), c.ID('None')))
		ctx.add(c.Label('end'))
		for name in reversed(ctx.cleanup):
			ctx.add(c.FuncCall(c.ID('Py_XDECREF'), c.ExprList(c.ID(name))))
		ctx.add(c.Return(c.ID('__return_value__')))
