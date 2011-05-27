'''
Copyright (c) 2011, Terrence Cole.
All rights reserved.
'''
from millipede.hl.types.hltype import HLType


class NoCommonBasesError(Exception):
	'''Raised when we attempt to find a common base for two totally disparate classes.'''


class PyObjectType(HLType):
	def __init__(self):
		pass


	@classmethod
	def common_base_type(cls, other:HLType) -> type:
		"""Find and return the common base type class between this object and 'other'."""
		if cls == other:
			return cls
		for ty0 in cls.__mro__:
			for ty1 in other.__mro__:
				if ty0 == ty1:
					return ty0
		raise NoCommonBasesError


	@staticmethod
	def common_base(types) -> type:
		'''Takes a list of PyObjectType and returns the class of the least common base between all types in the list.'''
		if not types:
			return PyObjectType
		base = types[0].__class__
		for ty in types[1:]:
			if base == ty.__class__:
				continue
			base = base.common_base_type(ty.__class__)
		return base

