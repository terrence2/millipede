'''
Copyright (c) 2011, Terrence Cole.
All rights reserved.
'''
from melano.c.pybuiltins import PY_BUILTINS
from melano.hl.nodes.module import MpModule
from melano.hl.nodes.name import Name


class Builtins(MpModule):
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)

		# TODO: augment symbols that we want to tie a tighter type to

		# add generic symbols for anything we don't special case
		for n in PY_BUILTINS:
			if not self.has_symbol(n):
				self.add_symbol(n)

	def lookup(self, name:str) -> Name:
		# Don't fall back to builtins!
		return self.symbols[name]

	def get_source_line(self, lineno:int) -> str:
		return 0

