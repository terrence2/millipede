'''
Copyright (c) 2011, Terrence Cole.
All rights reserved.
'''
from melano.hl.scope import Scope
import logging


class MelanoFunction(Scope):
	'''Specialization of function scope to contain expected calling style.'''
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)

		self.expect_args = [] # [str]
		self.expect_kwargs = [] # [str] -- these are ordered because keyworded args can get set from positional args in the caller

		# flags
		self.is_generator = False # set by yield stmt when indexing


	def show(self, level):
		logging.info("{}Function: {}".format('\t' * level, self.owner.name))
		super().show(level)
