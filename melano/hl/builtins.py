'''
Copyright (c) 2011, Terrence Cole.
All rights reserved.
'''
from melano.hl.name import Name
from melano.hl.scope import Scope


class Builtins(Scope):
	def lookup(self, name:str) -> Name:
		return self.symbols[name]
