'''
Copyright (c) 2011, Terrence Cole.
All rights reserved.
'''
from contextlib import contextmanager
from melano.c import ast as c
from melano.c.pybuiltins import PY_BUILTINS
from melano.c.types.lltype import LLType
from melano.c.types.pydict import PyDictLL
from melano.c.types.pyobject import PyObjectLL
from melano.c.types.pystring import PyStringLL
from melano.hl.name import Name


class PyModuleLL(PyObjectLL):
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)

		# the ll instance representing the dict of global variables
		self.ll_dict = None

		# the ll name and instance representing the function that builds the module
		self.c_builder_name = self.visitor.tu.reserve_name(self.hlnode.name + '_builder')
		self.c_builder_func = None


	def declare(self, tu):
		# create the namespace dict
		self.ll_dict = PyDictLL(self.hlnode, self.visitor)
		self.ll_dict.declare(tu, ['static'], name=self.hlnode.name + '_dict')

		# create the module creation function
		self.c_builder_func = c.FuncDef(
			c.Decl(self.c_builder_name,
				c.FuncDecl(
						c.ParamList(),
						c.PtrDecl(c.TypeDecl(self.c_builder_name, c.IdentifierType('PyObject')))), quals=['static']),
			c.Compound()
		)
		tu.add_fwddecl(self.c_builder_func.decl)
		tu.add(self.c_builder_func)

		# declare the module
		self.ll_mod = PyObjectLL(self.hlnode, self.visitor)
		self.ll_mod.declare(tu, ['static'])


	def return_existing(self, ctx):
		ctx.add(c.If(c.ID(self.ll_mod.name), c.Compound(c.Return(c.ID(self.ll_mod.name))), None))


	def new(self, ctx):
		# create the module in the creation function
		ctx.add(c.Assignment('=', c.ID(self.ll_mod.name), c.FuncCall(c.ID('PyModule_New'), c.ExprList(c.Constant('string', self.hlnode.name)))))
		self.fail_if_null(ctx, self.ll_mod.name)


	def get_dict(self, ctx):
		ctx.add(c.Assignment('=', c.ID(self.ll_dict.name), c.FuncCall(c.ID('PyModule_GetDict'), c.ExprList(c.ID(self.ll_mod.name)))))
		self.fail_if_null(ctx, self.ll_dict.name)


	def set_initial_string_attribute(self, ctx, name:str, s:str):
		if s is not None:
			ps = PyStringLL(None, self.visitor)
			ps.declare(self.visitor.scope.context)
			ps.new(ctx, PyStringLL.str2c(s))
		else:
			ps = PyObjectLL(None, self.visitor)
			ps.declare(self.visitor.scope.context)
			ps.assign_none(ctx)
		self.ll_dict.set_item_string(ctx, name, ps)


	def intro(self, ctx):
		ctx.add_variable(c.Decl('__return_value__', c.PtrDecl(c.TypeDecl('__return_value__', c.IdentifierType('PyObject'))), init=c.ID('NULL')), False)


	def outro(self, ctx):
		ctx.add(c.Assignment('=', c.ID('__return_value__'), c.ID(self.ll_mod.name)))
		ctx.add(c.Label('end'))
		for name in reversed(ctx.cleanup):
			ctx.add(c.FuncCall(c.ID('Py_XDECREF'), c.ExprList(c.ID(name))))
		ctx.add(c.Return(c.ID('__return_value__')))


	@contextmanager
	def maybe_recursive_call(self, ctx):
		yield


	def del_attr_string(self, ctx, name:str):
		self.ll_dict.del_item_string(ctx, name)


	def set_attr_string(self, ctx, name:str, val:LLType):
		return self.ll_dict.set_item_string(ctx, name, val)


	def get_attr_string(self, ctx, attrname:str, out:LLType):
		if str(attrname) in PY_BUILTINS:
			mode = 'likely'
		else:
			mode = 'unlikely'

		# access globals first, fall back to builtins -- remember to ref the global if we get it, since dict get item borrows
		ctx.add(c.Assignment('=', c.ID(out.name), c.FuncCall(c.ID('PyDict_GetItemString'), c.ExprList(c.ID(self.ll_dict.name), c.Constant('string', attrname)))))
		frombuiltins = c.If(c.FuncCall(c.ID(mode), c.ExprList(c.UnaryOp('!', c.ID(out.name)))),
				c.Compound(
					c.Assignment('=', c.ID(out.name), c.FuncCall(c.ID('PyObject_GetAttrString'),
														c.ExprList(c.ID(self.visitor.builtins.name), c.Constant('string', attrname)))),
				),
				c.Compound(
					c.FuncCall(c.ID('Py_INCREF'), c.ExprList(c.ID(out.name)))
				))
		ctx.add(frombuiltins)
		self.except_if_null(frombuiltins.iftrue, out.name, 'PyExc_NameError', "name '{}' is not defined".format(attrname))

