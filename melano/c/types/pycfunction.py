'''
Copyright (c) 2011, Terrence Cole.
All rights reserved.
'''
from melano.c import ast as c
from melano.c.types.pyobject import PyObjectLL
from melano.c.types.pystring import PyStringLL


class PyCFunctionLL(PyObjectLL):
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)

		# the c instance representing the array of local variables
		self.c_locals_name = None
		self.c_locals_array = None

		# the ll name and instance representing the c function that runs the python function
		self.c_runner_name = None
		self.c_runner_func = None

		# the name of the struct that defines the function
		self.funcdef_name = None

		# the ll name and instance representing the py callable function object
		self.c_obj_name = None
		self.c_obj = None


	def declare(self, ll_mod, tu, docstring):
		# create the locals array
		self.c_locals_name = tu.reserve_name(self.hlnode.owner.name + '_locals')
		cnt = self.hlnode.get_locals_count()
		self.c_locals_array = c.Decl(self.c_locals_name,
									c.ArrayDecl(c.PtrDecl(c.TypeDecl(self.c_locals_name, c.IdentifierType('PyObject'))), cnt),
									init=c.ExprList(*(cnt * [c.ID('NULL')])), quals=['static'])
		tu.add_fwddecl(self.c_locals_array)

		# NOTE: always use kwargs calling convention, because we don't know how external code will call us
		param_list = c.ParamList(
								c.Decl('self', c.PtrDecl(c.TypeDecl('self', c.IdentifierType('PyObject')))),
								c.Decl('args', c.PtrDecl(c.TypeDecl('args', c.IdentifierType('PyObject')))),
								c.Decl('kwargs', c.PtrDecl(c.TypeDecl('kwargs', c.IdentifierType('PyObject')))))

		# create the c function that will correspond to the py function
		self.c_runner_name = tu.reserve_name(self.hlnode.owner.name + '_runner')
		self.c_runner_func = c.FuncDef(
			c.Decl(self.c_runner_name,
				c.FuncDecl(param_list, \
						c.PtrDecl(c.TypeDecl(self.c_runner_name, c.IdentifierType('PyObject')))), quals=['static']),
			c.Compound()
		)
		tu.add_fwddecl(self.c_runner_func.decl)
		tu.add(self.c_runner_func)

		# NOTE: we create _all_ functions, even nested/class functions, in the module, instead of their surrounding scope
		#		so that we don't have to re-create the full infrastructure every time we visit the outer scope 
		ctx = ll_mod.c_builder_func.body
		ctx.add(c.Comment('Declare Function "{}"'.format(self.hlnode.owner.name)))

		# create the function definition structure
		self.funcdef_name = ctx.reserve_name(self.hlnode.owner.name + '_def')
		c_docstring = c.Constant('string', PyStringLL.str2c(docstring)) if docstring else c.ID('NULL')
		ctx.add_variable(c.Decl(self.funcdef_name, c.TypeDecl(self.funcdef_name, c.Struct('PyMethodDef')),
				init=c.ExprList(
							c.Constant('string', str(self.hlnode.owner.name)),
							c.Cast(c.IdentifierType('PyCFunction'), c.ID(self.c_runner_name)),
							c.BinaryOp('|', c.ID('METH_VARARGS'), c.ID('METH_KEYWORDS')), c_docstring)), False)

		# create the function pyobject itself
		self.c_obj_name = self.hlnode.owner.name + "_pycfunc"
		self.c_obj = PyObjectLL(self.hlnode)
		self.c_obj.declare(tu, ['static'], name=self.c_obj_name)
		ctx.add(c.Assignment('=', c.ID(self.c_obj_name), c.FuncCall(c.ID('PyCFunction_NewEx'), c.ExprList(
													c.UnaryOp('&', c.ID(self.funcdef_name)), c.ID('NULL'), c.ID('NULL')))))
		self.fail_if_null(ctx, self.c_obj_name)

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


	def new(self, ctx):
		# fwddecl and init the return value
		ctx.add_variable(c.Decl('__return_value__', c.PtrDecl(c.TypeDecl('__return_value__', c.IdentifierType('PyObject'))), init=c.ID('NULL')), False)


	def emit_outro(self, ctx):
		ctx.add(c.Assignment('=', c.ID('__return_value__'), c.ID('None')))
		ctx.add(c.Label('end'))
		for name in reversed(ctx.cleanup):
			ctx.add(c.FuncCall(c.ID('Py_XDECREF'), c.ExprList(c.ID(name))))
		ctx.add(c.Return(c.ID('__return_value__')))
