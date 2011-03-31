'''
Copyright (c) 2011, Terrence Cole.
All rights reserved.
'''
from contextlib import contextmanager
from melano.c import ast as c
from melano.c.types.pyobject import PyObjectLL
from melano.c.types.pystring import PyStringLL


class PyClassLL(PyObjectLL):
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)

		# the low-level func responsible for building the class
		self.c_builder_func = None

		# the pycfunction wrapper around the lowlevel builder func that makes it pycallable
		self.c_builder_obj = None

		# the pyobject that our builder will return into
		self.c_obj = None

		# passed into the class creation function and used by us to set attrs in the local namespace
		self.c_namespace_dict = None


	def create_builderfunc(self, tu):
		param_list = c.ParamList(
								c.Decl('self', c.PtrDecl(c.TypeDecl('self', c.IdentifierType('PyObject')))),
								c.Decl('args', c.PtrDecl(c.TypeDecl('args', c.IdentifierType('PyObject')))),
								c.Decl('kwargs', c.PtrDecl(c.TypeDecl('kwargs', c.IdentifierType('PyObject')))))
		name = tu.reserve_name(self.hlnode.owner.name + '_builder')
		self.c_builder_func = c.FuncDef(
			c.Decl(name,
				c.FuncDecl(param_list,
						c.PtrDecl(c.TypeDecl(name, c.IdentifierType('PyObject')))), quals=['static']),
			c.Compound()
		)
		tu.add_fwddecl(self.c_builder_func.decl)
		tu.add(self.c_builder_func)


	def create_builder_funcdef(self, ctx, tu):
		ctx.add(c.Comment('Declare Class creation pycfunction "{}"'.format(self.hlnode.owner.name)))

		# create the function pyobject itself
		name = self.hlnode.owner.name + "_builder_pycfunc"
		self.c_builder_obj = PyObjectLL(self.hlnode, self.visitor)
		self.c_builder_obj.declare(ctx, name=name)
		c_name = c.Constant('string', PyStringLL.str2c(self.hlnode.owner.name))
		ctx.add(c.Assignment('=', c.ID(self.c_builder_obj.name), c.FuncCall(c.ID('PyMelanoFunction_New'), c.ExprList(
													c_name, c.ID(self.c_builder_func.decl.name), c.ID('NULL')))))
		self.fail_if_null(ctx, self.c_builder_obj.name)

		return self.c_builder_obj


	def declare_pyclass(self, tu):
		self.c_obj = PyObjectLL(self.hlnode, self.visitor)
		self.c_obj.declare(tu, quals=['static'], name=self.hlnode.owner.name)
		return self.c_obj


	def set_namespace(self, ns_dict):
		self.c_namespace_dict = ns_dict


	def intro(self, ctx, docstring, module_name):
		ctx.add_variable(c.Decl('__return_value__', c.PtrDecl(c.TypeDecl('__return_value__', c.IdentifierType('PyObject'))), init=c.ID('NULL')), False)

		# set the docstring
		ds = PyStringLL(None, self.visitor)
		ds.declare(self.visitor.scope.context)
		if docstring:
			ds.new(ctx, docstring)
		else:
			ds.assign_none(ctx)
		self.c_namespace_dict.set_item_string(ctx, '__doc__', ds)

		# set the module name
		ds = PyStringLL(None, self.visitor)
		ds.declare(self.visitor.scope.context)
		if module_name:
			ds.new(ctx, module_name)
			self.c_namespace_dict.set_item_string(ctx, '__module__', ds)


	def outro(self, ctx):
		ctx.add(c.Assignment('=', c.ID('__return_value__'), c.ID(self.visitor.none.name)))
		ctx.add(c.Label('end'))
		for name in reversed(ctx.cleanup):
			ctx.add(c.FuncCall(c.ID('Py_XDECREF'), c.ExprList(c.ID(name))))
		ctx.add(c.Return(c.ID('__return_value__')))


	@contextmanager
	def maybe_recursive_call(self, ctx):
		yield


	def del_attr_string(self, ctx, attrname):
		return self.c_namespace_dict.del_item_string(ctx, attrname)


	def set_attr_string(self, ctx, attrname, attrval):
		return self.c_namespace_dict.set_item_string(ctx, attrname, attrval)


	def get_attr_string(self, ctx, attrname, out):
		self.c_namespace_dict.get_item_string(ctx, attrname, out, 'PyExc_NameError', "name '{}' is not defined".format(attrname))
