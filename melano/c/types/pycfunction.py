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


	def declare(self, ll_mod, tu, docstring):
		# create the locals array
		self.c_locals_name = tu.reserve_name(self.hlnode.owner.name + '_locals')
		cnt = self.hlnode.get_locals_count()
		self.c_locals_array = c.Decl(self.c_locals_name,
									c.ArrayDecl(c.PtrDecl(c.TypeDecl(self.c_locals_name, c.IdentifierType('PyObject'))), cnt),
									init=c.ExprList(*(cnt * [c.ID('NULL')])))
		tu.add_fwddecl(self.c_locals_array)

		# create the c function that will correspond to the py function 
		self.c_runner_name = tu.reserve_name(self.hlnode.owner.name + '_runner')
		self.c_runner_func = c.FuncDef(
			c.Decl(self.c_runner_name,
				c.FuncDecl(c.ParamList(
									c.Decl('self', c.PtrDecl(c.TypeDecl('self', c.IdentifierType('PyObject')))),
									c.Decl('args', c.PtrDecl(c.TypeDecl('args', c.IdentifierType('PyObject'))))), \
						c.PtrDecl(c.TypeDecl(self.c_runner_name, c.IdentifierType('PyObject'))))),
			c.Compound()
		)
		tu.add_fwddecl(self.c_runner_func.decl)
		tu.add(self.c_runner_func)

		# NOTE: we create _all_ functions, even nested/class functions, in the module, instead of their surrounding scope
		#		so that we don't have to re-create the full infrastructure every time we visit the outer scope 
		ctx = ll_mod.c_builder_func.body
		ctx.add(c.Comment('Declare Function "{}"'.format(self.hlnode.owner.name)))

		# create the function definition structure
		funcdef_name = ctx.reserve_name(self.hlnode.owner.name + '_def')
		c_docstring = c.Constant('string', PyStringLL.str2c(docstring)) if docstring else c.ID('NULL')
		ctx.add_variable(c.Decl(funcdef_name, c.TypeDecl(funcdef_name, c.Struct('PyMethodDef')),
				init=c.ExprList(c.Constant('string', str(self.hlnode.owner.name)), c.ID(self.c_runner_name), c.ID('METH_VARARGS'), c_docstring)), False)

		# create the function pyobject itself
		tmp = PyObjectLL(None)
		tmp.declare(ctx, name=self.hlnode.owner.name + '_cfunc')
		ctx.add(c.Assignment('=', c.ID(tmp.name), c.FuncCall(c.ID('PyCFunction_NewEx'), c.ExprList(
													c.UnaryOp('&', c.ID(funcdef_name)), c.ID('NULL'), c.ID('NULL')))))
		self.fail_if_null(ctx, tmp.name)

		return tmp

		#FIXME: do we want to pass our own dict as self here?  What is the role for the last param?  Just the module name?
		#cfunc_inst = PyCFunctionType(funcname.global_name)
		#cfunc_inst.declare(self.tu, ['static'])
		#cfunc_inst.new(self.module_func.body, funcdef_name, funcscope.inst, 'NULL')


	def set_attr_string(self, ctx, attrname, val):
		raise NotImplementedError

	def new(self, ctx, funcdef_name, locals, modname):
		pass
