'''
Copyright (c) 2011, Terrence Cole.
All rights reserved.
'''
from melano.hl.module import MpModule
from melano.hl.name import Name


class Builtins(MpModule):

	def lookup(self, name:str) -> Name:
		# Don't fall back to builtins!
		return self.symbols[name]

	def get_source_line(self, lineno:int) -> str:
		return 0

