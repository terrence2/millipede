'''
Copyright (c) 2011, Terrence Cole.
All rights reserved.
'''
from melano.project.scope import Scope


class MelanoFunction(Scope):
	'''Specialization of function scope to contain expected calling style.'''
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)

		self.expect_args = [] # [str]
		self.expect_kwargs = [] # [str] -- these are ordered because keyworded args can get set from positional args in the caller
