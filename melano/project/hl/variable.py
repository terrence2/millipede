'''
Copyright (c) 2011, Terrence Cole.
All rights reserved.
'''
from melano.project.lowlevel.type.object import PyObject
from melano.project.lowlevel.type.ptr import Ptr


class MelanoVariable:
	def __init__(self, node, owner):
		self.node = node
		self.owner = None
		self.types = []

		# backref, so visitors can find us
		self.node.hl = self


	def get_type(self):
		return Ptr(PyObject())
		#assert len(self.types) > 0
		#if len(self.types) > 1:
		#	return PyObject()
		#return self.types[0]


	def __str__(self):
		return '<Var[{}]>'.format(str(self.node))
