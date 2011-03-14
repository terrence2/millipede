'''
Copyright (c) 2011, Terrence Cole.
All rights reserved.
'''
from melano.hl.types.pyobject import PyObjectType


class PyFunctionType(PyObjectType):
	def __init__(self, scope):
		super().__init__()
		self.scope = scope
