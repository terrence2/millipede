'''
Copyright (c) 2011, Terrence Cole.
All rights reserved.
'''
from millipede.c import ast as c
from millipede.c.types.lltype import LLType
from millipede.hl.types.hltype import HLType


class CIntegerLL(LLType):
	MAX = 2 ** 63 - 1

	def __init__(self, hlnode, visitor, size=None, signed=None, is_a_bool=False):
		super().__init__(hlnode, visitor)
		self.size = self.hltype.size if self.hltype else size
		self.signed = self.hltype.signed if self.hltype else signed
		# allow us to use ints as bools at the C level and still get the right promotion to pyobject later
		self.is_a_bool = self.hltype.is_a_bool if self.hltype else is_a_bool


	def declare_tmp(self, *, name=None):
		need_declare = super().declare_tmp(name=name)
		if need_declare:
			self.v.scope.ctx.add_variable(c.Decl(self.name, c.TypeDecl(self.name, c.IdentifierType('int')), quals=[]), need_cleanup=False)


	def declare(self, *, is_global=False, quals=[], name=None, init=0):
		super().declare(is_global=is_global, quals=quals, name=name)
		#TODO: specialize for signed and sized ints
		self.v.scope.ctx.add_variable(c.Decl(self.name, c.TypeDecl(self.name, c.IdentifierType('int')), quals=quals, init=c.Constant('integer', init)), False)


	def decref(self):
		self.tmp_decref()
	def xdecref(self):
		self.tmp_decref()
	def clear(self):
		self.tmp_decref()


	def as_pyobject(self):
		if self.is_a_bool:
			out = PyBoolLL(None, self.v)
			out.declare_tmp()
			out._new_from_long(c.ID(self.name))
			return out
		else:
			out = PyIntegerLL(None, self.v)
			out.declare_tmp()
			out._new_from_long(c.ID(self.name))
			return out


	def as_ssize(self):
		return self


	def not_(self, out_inst=None):
		if not out_inst:
			out_inst = CIntegerLL(None, self.v)
			out_inst.declare_tmp(name="_inv_rv")
		self.v.ctx.add(c.Assignment('=', c.ID(out_inst.name), c.UnaryOp('!', c.ID(self.name))))
		return out_inst


	def is_true(self, out_inst=None):
		if out_inst:
			self.v.ctx.add(c.Assignment('=', c.ID(out_inst.name), c.ID(self.name)))
		return self


	def set_constant(self, i):
		self.v.ctx.add(c.Assignment('=', c.ID(self.name), c.Constant('integer', i)))


from millipede.c.types.pybool import PyBoolLL
from millipede.c.types.pyinteger import PyIntegerLL

