'''
Copyright (c) 2011, Terrence Cole.
All rights reserved.
'''
from melano.hl.types.pyobject import PyObjectType


class PyFunctionType(PyObjectType):
	CALL_TYPE_UNKNOWN = 0
	CALL_TYPE_BUILTIN = 1
	CALL_TYPE_LOCAL = 2
	CALL_TYPE_REMOTE = 3


	def __init__(self, scope):
		super().__init__()
		self.scope = scope

		self._call_type = self.CALL_TYPE_UNKNOWN


	@property
	def call_type(self):
		return self._call_type
