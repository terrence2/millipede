'''
Copyright (c) 2011, Terrence Cole.
All rights reserved.
'''
from millipede.c.types.pyobject import PyObjectLL


class PyTypeLL(PyObjectLL):
	@staticmethod
	def typename():
		return 'PyType_Type'
