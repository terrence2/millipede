'''
Copyright (c) 2011, Terrence Cole.
All rights reserved.
'''
from melano.hl.types.hltype import HLType


class NoCommonBasesError(Exception):
	'''Raised when we attempt to find a common base for two totally disparate classes.'''


class PyObjectType(HLType):

	@classmethod
	def common_base_type(cls, other):
		if cls == other:
			return cls()
		for ty0 in cls.__mro__:
			for ty1 in other.__mro__:
				if ty0 == ty1:
					return ty0()
		raise NoCommonBasesError
