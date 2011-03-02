'''
Copyright (c) 2011, Terrence Cole.
All rights reserved.
'''
from melano.hl.types.pyobject import PyObjectType


class PyFunctionType(PyObjectType):
	def __init__(self):
		self.has_noargs = False
		self.has_kwargs = False
