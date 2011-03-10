'''
Copyright (c) 2011, Terrence Cole.
All rights reserved.
'''
from melano.hl.name import Name
from melano.hl.scope import Scope
from melano.hl.types.pyfunction import PyFunctionType
import itertools
import logging



class MelanoFunction(Scope):
	'''Specialization of function scope to contain expected calling style.'''
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)

		# flags
		self.is_generator = False # set by yield stmt when indexing

		# the hl type definition -- used mostly as an identity badge in the function
		self.type = PyFunctionType()

		# map locals names to an offset into the locals array
		self.locals_map = {}
		self.locals_count = itertools.count(0)


	def get_locals_count(self):
		return len(self.locals_map)


	def show(self, level):
		logging.info("{}Function: {}".format('\t' * level, self.owner.name))
		super().show(level)


	def add_symbol(self, name, init=None):
		if name not in self.locals_map:
			self.locals_map[name] = next(self.locals_count)
		return super().add_symbol(name, init)

	def lookup(self, name:str) -> Name:
		try:
			return self.symbols[name]
		except KeyError:
			return self.owner.parent.lookup(name)
