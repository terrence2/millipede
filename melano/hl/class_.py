'''
Copyright (c) 2011, Terrence Cole.
All rights reserved.
'''
from melano.hl.name import Name
from melano.hl.scope import Scope


class MelanoClass(Scope):
	def lookup(self, name:str) -> Name:
		try:
			return self.symbols[name]
		except KeyError:
			return self.owner.parent.lookup(name)
