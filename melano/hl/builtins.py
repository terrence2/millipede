'''
Copyright (c) 2011, Terrence Cole.
All rights reserved.
'''
from melano.hl.module import MelanoModule
from melano.hl.name import Name


class Builtins(MelanoModule):

	def lookup(self, name:str) -> Name:
		# Don't fall back to builtins!
		return self.symbols[name]

	def get_source_line(self, lineno:int) -> str:
		return 0

