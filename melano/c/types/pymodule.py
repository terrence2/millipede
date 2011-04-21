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
		self.c_builder_name = self.v.tu.reserve_global_name(self.hlnode.name + '_builder')
		self.c_builder_func = None


	def declare(self):
		# create the namespace dict
		self.ll_dict = PyDictLL(self.hlnode, self.v)
		self.ll_dict.declare(is_global=True, quals=['static'], name=self.hlnode.name + '_dict')

		# create the module creation function
		self.c_builder_func = c.FuncDef(
			c.Decl(self.c_builder_name,
				c.FuncDecl(
						c.ParamList(),
						c.PtrDecl(c.TypeDecl(self.c_builder_name, c.IdentifierType('PyObject')))), quals=['static']),
			c.Compound()
		)
		self.v.tu.add_fwddecl(self.c_builder_func.decl)
		self.v.tu.add(self.c_builder_func)

		# declare the module
		self.ll_mod = PyObjectLL(self.hlnode, self.v)
		self.ll_mod.declare(is_global=True, quals=['static'])


	def return_existing(self):
		self.v.ctx.add(c.If(c.ID(self.ll_mod.name), c.Compound(c.Return(c.ID(self.ll_mod.name))), None))


	def new(self):
		self.name = self.ll_mod.name
		n = '__main__' if self.hlnode.is_main else self.hlnode.python_name
		self.v.ctx.add(c.Comment('Create module "{}" with __name__ "{}"'.format(self.hlnode.python_name, n)))
		self.v.ctx.add(c.Assignment('=', c.ID(self.ll_mod.name), c.FuncCall(c.ID('PyModule_New'),
																	c.ExprList(c.Constant('string', n)))))
		self.fail_if_null(self.ll_mod.name)

		# get the modules dict
		mods = PyDictLL(None, self.v)
		mods.declare(name='_modules')
		self.v.ctx.add(c.Comment('Insert into sys.modules'))
		self.v.ctx.add(c.Assignment('=', c.ID(mods.name), c.FuncCall(c.ID('PyImport_GetModuleDict'), c.ExprList())))
		self.fail_if_null(self.ll_mod.name)
		mods.incref()

		# add ourself to the modules dict
		mods.set_item_string(n, self)

		# clear the ref so we don't free it later
		mods.clear()

		# grab the module dict
		self.v.ctx.add(c.Assignment('=', c.ID(self.ll_dict.name), c.FuncCall(c.ID('PyModule_GetDict'), c.ExprList(c.ID(self.ll_mod.name)))))
		self.fail_if_null(self.ll_dict.name)

		# set the builtins on the module
		self.set_attr_string('__builtins__', self.v.builtins)

		# set builtin properties
		self.set_initial_string_attribute('__name__', n)
		#self.ll_module.set_initial_string_attribute(self.context, '__name__', self.hl_module.owner.python_name)


	def set_initial_string_attribute(self, name:str, s:str):
		if s is not None:
			ps = PyStringLL(None, self.v)
			ps.declare()
			ps.new(s)
		else:
			ps = PyObjectLL(None, self.v)
			ps.declare()
			ps.assign_none()
		self.set_attr_string(name, ps)


	def intro(self):
		self.v.scope.ctx.add_variable(c.Decl('__return_value__', c.PtrDecl(c.TypeDecl('__return_value__', c.IdentifierType('PyObject'))), init=c.ID('NULL')), False)


	def outro(self):
		self.v.ctx.add(c.Assignment('=', c.ID('__return_value__'), c.ID(self.ll_mod.name)))
		self.v.ctx.add(c.Label('end'))
		for name in reversed(self.v.scope.ctx.cleanup):
			self.v.ctx.add(c.FuncCall(c.ID('Py_XDECREF'), c.ExprList(c.ID(name))))
		self.v.ctx.add(c.Return(c.ID('__return_value__')))


	@contextmanager
	def maybe_recursive_call(self):
		yield


	def del_attr_string(self, name:str):
		self.ll_dict.del_item_string(name)


	def set_attr_string(self, name:str, val:LLType):
		self.ll_dict.set_item_string(name, val)
		#FIXME: do we really need both dict and attr?  don't these go to the same place?
		super().set_attr_string(name, val)


	def get_attr_string(self, attrname:str, out:LLType):
		if str(attrname) in PY_BUILTINS:
			mode = 'likely'
		else:
			mode = 'unlikely'

		# access globals first, fall back to builtins -- remember to ref the global if we get it, since dict get item borrows
		#out.xdecref()
		self.ll_dict.get_item_string_nofail(attrname, out)
		frombuiltins = self.v.ctx.add(c.If(c.FuncCall(c.ID(mode), 
				c.ExprList(c.UnaryOp('!', c.ID(out.name)))), c.Compound(), None))
		with self.v.new_context(frombuiltins.iftrue):
			self.v.builtins.get_attr_string_with_exception(attrname, out, 'PyExc_NameError', "name '{}' is not defined".format(attrname))
			#self.except_if_null(out.name, 'PyExc_NameError', "name '{}' is not defined".format(attrname))
		#with self.v.new_context(frombuiltins.iffalse):
		#	out.incref()

