'''
Copyright (c) 2011, Terrence Cole.
All rights reserved.
'''
from collections import OrderedDict
from melano.project.name import Name


class Scope:
	'''
	A symbol table.
	'''
	def __init__(self, owner:Name):
		self.symbols = OrderedDict()
		self.owner = owner


	def lookup(self, name:str) -> Name:
		return self.symbols[name]


	def has_closure(self) -> bool:
		for sym in self.symbols.values():
			if sym.scope:
				return True
		return False


	def add_symbol(self, name:str, init:object=None):
		self.symbols[name] = Name(name, self)
		return self.symbols[name]


	def show(self, level=0):
		for name in self.symbols:
			self.symbols[name].show(level + 1)
