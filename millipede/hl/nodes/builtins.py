'''
Copyright (c) 2011, Terrence Cole.
All rights reserved.
'''
from collections import namedtuple
from millipede.c.pybuiltins import PY_BUILTINS
from millipede.hl.nodes.module import MpModule
from millipede.hl.nodes.name import Name
from millipede.hl.nodes.scope import Scope
from millipede.ir.basicblock import BuiltinBlock


#_FakeAST = namedtuple('_FakeAST', ['bb'])

class _BuiltinFunction(Scope):
	def __init__(self, sym):
		super().__init__(sym)
		self._blocks = [BuiltinBlock(sym.global_c_name, sym.name, None, None)]
		self._block_tails = [self._blocks[0]]


class Builtins(MpModule):
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)

		# TODO: augment symbols that we want to tie a tighter type to

		# add generic symbols for anything we don't special case
		for n in PY_BUILTINS:
			if not self.has_symbol(n):
				sym = self.add_symbol(n)
				sym.scope = _BuiltinFunction(sym)
				#sym.scope = BuiltinBlock(sym.global_c_name, sym.name, None, None)
				#sym.ast = _FakeAST(sym.scope)

		self._blocks = [BuiltinBlock('__builtins__', 'builtins', None, None)]
		self._block_tails = [self._blocks[-1]]
		self._instructions = self._blocks[0]._instructions


	def lookup(self, name:str) -> Name:
		# Don't fall back to builtins!
		return self.symbols[name]


	def get_source_line(self, lineno:int) -> str:
		return 0

