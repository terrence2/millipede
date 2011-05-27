'''
Copyright (c) 2011, Terrence Cole.
All rights reserved.
'''
from millipede.hl.types.pyobject import PyObjectType


class PyClassType(PyObjectType):
	def __init__(self, scope):
		super().__init__()
		self.scope = scope
