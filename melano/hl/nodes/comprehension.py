'''
Copyright (c) 2011, Terrence Cole.
All rights reserved.
'''
from melano.hl.nodes.entity import Entity
from melano.hl.nodes.scope import Scope
from melano.hl.types.pycomprehension import PyComprehensionType


class MpComprehension(Scope, Entity):
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.add_type(PyComprehensionType())

	def lookup(self, name):
		try:
			return self.symbols[name]
		except KeyError:
			return self.owner.parent.lookup(name)
