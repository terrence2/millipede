'''
Copyright (c) 2011, Terrence Cole.
All rights reserved.
'''
from millipede.hl.nodes.entity import Entity
from millipede.hl.nodes.name import Name
from millipede.hl.nodes.scope import Scope
from millipede.hl.types.pyclosure import PyClosureType
from millipede.hl.types.pyfunction import PyFunctionType
from millipede.hl.types.pygenerator import PyGeneratorType
from millipede.hl.types.pygeneratorclosure import PyGeneratorClosureType
from millipede.ir.opcodes import RETURN_VALUE
import itertools
import logging



class MpFunction(Scope, Entity):
	'''Specialization of function scope to contain expected calling style.'''
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)

		# flags
		self.is_generator = False # set by presense of yield function when indexing
		self.has_closure = False # set by presence of sub-functions when indexing
		self.is_anonymous = False # set by lambda, genexp which doesn't implicitly create a name

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


	#### Frame related
	def set_blocks(self, blocks):
		super().set_blocks(blocks)
		#FIXME: what about raise?  in what contexts?  What sort of raise?  How do we handle this generally?
		for bb in blocks:
			if isinstance(bb._instructions[-1], RETURN_VALUE):
				self._block_tails.append(blocks[-1])

		assert blocks[-1] in self._block_tails, "We failed to insert a 'return None' at the end of a function!"
