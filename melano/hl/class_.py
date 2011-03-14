'''
Copyright (c) 2011, Terrence Cole.
All rights reserved.
'''
from melano.hl.name import Name
from melano.hl.scope import Scope
from melano.hl.types.pyclass import PyClassType
import logging


class MelanoClass(Scope):
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)

		# the hl type definition
		self.type = PyClassType(self)

		# Lookups are only valid within the class building scope... to avoid improperly aliasing builtins defined in the
		#		class at "runtime" we need to ensure that lookups bypass the class after we are done with visiting the
		#		the internals of the class.
		self.is_building = True


	def add_function_def(self, inst):
		self._funcs.append(inst)


	def show(self, level):
		logging.info("{}Class: {}".format('\t' * level, self.owner.name))
		super().show(level)


	def lookup(self, name:str) -> Name:
		# NOTE: names in classes are only directly accessable when we are used as a scope, so in general this lookup is wrong
		if self.is_building:
			try:
				return self.symbols[name]
			except KeyError:
				return self.owner.parent.lookup(name)
		else:
			return self.owner.parent.lookup(name)
