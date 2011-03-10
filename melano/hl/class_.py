'''
Copyright (c) 2011, Terrence Cole.
All rights reserved.
'''
from melano.hl.name import Name
from melano.hl.scope import Scope
from melano.hl.types.pyclass import PyClassType


class MelanoClass(Scope):
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)

		self.type = PyClassType()


	def add_function_def(self, inst):
		self._funcs.append(inst)


	def lookup(self, name:str) -> Name:
		try:
			return self.symbols[name]
		except KeyError:
			return self.owner.parent.lookup(name)
