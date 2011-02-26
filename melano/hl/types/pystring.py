'''
Copyright (c) 2011, Terrence Cole.
All rights reserved.
'''
from melano.hl.types.pyobject import PyObjectType


class PyStringType(PyObjectType):
	ATTRS = {
				'strip': None
			}

	@classmethod
	def reference_attribute(cls, attr:str):
		return cls.ATTRS[attr]

