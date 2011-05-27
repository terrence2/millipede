'''
Copyright (c) 2011, Terrence Cole.
All rights reserved.
'''
from millipede.hl.types.hltype import HLType
from millipede.hl.types.pyobject import PyObjectType


class PyFunctionType(PyObjectType):
	CALL_TYPE_UNKNOWN = 0
	CALL_TYPE_BUILTIN = 1
	CALL_TYPE_LOCAL = 2
	CALL_TYPE_REMOTE = 3


	def __init__(self, scope):
		super().__init__()
		self.scope = scope

		# types for a function type encapsulates the possible returned types from the function
		self.types = []

		self._call_type = self.CALL_TYPE_UNKNOWN


	def add_type(self, ty:HLType):
		self.types.append(ty)


	def get_type(self):
		return PyObjectType.common_base(self.types)()


	@property
	def call_type(self):
		return self._call_type
