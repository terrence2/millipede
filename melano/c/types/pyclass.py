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


	def create_builderfunc(self):
		param_list = c.ParamList(
								c.Decl('self', c.PtrDecl(c.TypeDecl('self', c.IdentifierType('PyObject')))),
								c.Decl('args', c.PtrDecl(c.TypeDecl('args', c.IdentifierType('PyObject')))),
								c.Decl('kwargs', c.PtrDecl(c.TypeDecl('kwargs', c.IdentifierType('PyObject')))))
		name = self.v.tu.reserve_global_name(self.hlnode.owner.global_c_name + '_builder')
		self.c_builder_func = c.FuncDef(
			c.Decl(name,
				c.FuncDecl(param_list,
						c.PtrDecl(c.TypeDecl(name, c.IdentifierType('PyObject')))), quals=['static']),
			c.Compound()
		)
		self.v.tu.add_fwddecl(self.c_builder_func.decl)
		self.v.tu.add(self.c_builder_func)


	def create_builder_funcdef(self):
		self.v.ctx.add(c.Comment('Declare Class creation pycfunction "{}"'.format(self.hlnode.owner.name)))

		# create the function pyobject itself
		self.c_builder_obj = PyObjectLL(self.hlnode, self.v)
		self.c_builder_obj.declare(name=self.hlnode.owner.name + "_builder_pycfunc")
		self.c_builder_obj.xdecref()
		c_name = c.Constant('string', PyStringLL.name_to_c_string(self.hlnode.owner.name))
		self.v.ctx.add(c.Assignment('=', c.ID(self.c_builder_obj.name), c.FuncCall(c.ID('PyMelanoFunction_New'), c.ExprList(
													c_name, c.ID(self.c_builder_func.decl.name), c.ID('NULL')))))
		self.fail_if_null(self.c_builder_obj.name)

		return self.c_builder_obj


	def declare_pyclass(self):
		self.c_obj = PyObjectLL(self.hlnode, self.v)
		self.c_obj.declare(is_global=True, quals=['static'], name=self.hlnode.owner.global_c_name)
		return self.c_obj


	def set_namespace(self, ns_dict):
		self.c_namespace_dict = ns_dict


	def intro(self, docstring, module_name):
		self.v.ctx.add_variable(c.Decl('__return_value__', c.PtrDecl(c.TypeDecl('__return_value__', c.IdentifierType('PyObject'))), init=c.ID('NULL')), False)

		# set the docstring
		ds = PyStringLL(None, self.v)
		ds.declare()
		if docstring:
			ds.new(docstring)
		else:
			ds.assign_none()
		self.c_namespace_dict.set_item_string('__doc__', ds)

		# set the module name
		ds = PyStringLL(None, self.v)
		ds.declare()
		if module_name:
			ds.new(module_name)
			self.c_namespace_dict.set_item_string('__module__', ds)


	def outro(self):
		self.v.none.incref()
		self.v.ctx.add(c.Assignment('=', c.ID('__return_value__'), c.ID(self.v.none.name)))
		self.v.ctx.add(c.Label('end'))
		for name in reversed(self.v.ctx.cleanup):
			self.v.ctx.add(c.FuncCall(c.ID('Py_XDECREF'), c.ExprList(c.ID(name))))
		self.v.ctx.add(c.Return(c.ID('__return_value__')))


	@contextmanager
	def maybe_recursive_call(self):
		yield


	def del_attr_string(self, attrname):
		return self.c_namespace_dict.del_item_string(attrname)


	def set_attr_string(self, attrname, attrval):
		return self.c_namespace_dict.set_item_string(attrname, attrval)


	def get_attr_string(self, attrname, out):
		self.c_namespace_dict.get_item_string(attrname, out, 'PyExc_NameError', "name '{}' is not defined".format(attrname))


