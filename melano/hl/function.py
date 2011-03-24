'''
Copyright (c) 2011, Terrence Cole.
All rights reserved.
'''
from melano.hl.name import Name
from melano.hl.scope import Scope
from melano.hl.types.pyclosure import PyClosureType
from melano.hl.types.pyfunction import PyFunctionType
from melano.hl.types.pygenerator import PyGeneratorType
from melano.hl.types.pygeneratorclosure import PyGeneratorClosureType
import itertools
import logging



class MelanoFunction(Scope):
	'''Specialization of function scope to contain expected calling style.'''
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)

		# flags
		self.is_generator = False # set by presense of yield function when indexing
		self.has_closure = False # set by presence of sub-functions when indexing

		# store the type asside so that we can store stuff in it, after we create it
		self.type = None


	def set_needs_closure(self):
		self.has_closure = True
		super().set_needs_closure()


	def get_locals_count(self):
		return len(self.locals_map)


	def show(self, level):
		logging.info("{}Function: {}".format('\t' * level, self.owner.name))
		super().show(level)


	def lookup(self, name:str) -> Name:
		try:
			return self.symbols[name]
		except KeyError:
			return self.get_next_scope().lookup(name)


	def get_type(self):
		if self.type:
			return self.type

		if self.has_closure:
			if self.is_generator:
				self.type = PyGeneratorClosureType(self)
			else:
				self.type = PyClosureType(self)
		elif self.is_generator:
			self.type = PyGeneratorType(self)
		else:
			self.type = PyFunctionType(self)

		return self.type

