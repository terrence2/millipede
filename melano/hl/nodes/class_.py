'''
Copyright (c) 2011, Terrence Cole.
All rights reserved.
'''
from melano.hl.nodes.entity import Entity
from melano.hl.nodes.name import Name
from melano.hl.nodes.scope import Scope
from melano.hl.types.pyclass import PyClassType
import logging


class MpClass(Scope, Entity):
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.add_type(PyClassType(self))


	def add_function_def(self, inst):
		self._funcs.append(inst)


	def show(self, level):
		logging.info("{}Class: {}".format('\t' * level, self.owner.name))
		super().show(level)


	def lookup(self, name:str) -> Name:
		# NOTE: names in classes are only directly accessible when we are used as a scope, so in general this lookup is wrong
		try:
			return self.symbols[name]
		except KeyError:
			return self.get_next_scope().lookup(name)
