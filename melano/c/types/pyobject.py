'''
Copyright (c) 2011, Terrence Cole.
All rights reserved.
'''
from melano.c import ast as c
from melano.c.types.lltype import LLType


class PyObjectType(LLType):
	def declare(self, func, quals=[]):
		func.add_variable(c.Decl(self.name, c.PtrDecl(c.TypeDecl(self.name, c.IdentifierType('PyObject')))))

	def set_none(self, func):
		func.add(c.Assignment('=', c.ID(self.name), c.ID('None')))
