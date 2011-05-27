'''
Copyright (c) 2011, Terrence Cole.
All rights reserved.
'''
from millipede.hl.nodes.entity import Entity
from millipede.hl.types.pyfunction import PyFunctionType
from millipede.hl.types.pyobject import PyObjectType


class Call(Entity):
	"""Encapsulates a call in the name graph.  This basically substitues the return of the type of the call
		for the type of the callee at get_type time."""

	def __init__(self, func:Entity, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.func = func


	def get_type(self):
		functype = self.func.get_type()
		if isinstance(functype, PyFunctionType):
			return functype.get_type()
		return PyObjectType()
