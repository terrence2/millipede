'''
Copyright (c) 2011, Terrence Cole.
All rights reserved.
'''
from melano.project.type.object import PyObject


class ForeignObject:
	def __init__(self, name):
		self.name = name
		self.types = [PyObject]
