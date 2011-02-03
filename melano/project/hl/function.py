'''
Copyright (c) 2011, Terrence Cole.
All rights reserved.
'''


class MelanoFunction:
	def __init__(self, node):
		self.node = node
		self.parent = None
		self.names = {}

		# backref, so visitors can find us
		self.node.hl = self


	def lookup(self, name):
		if name in self.names:
			return self.names[name]
		return self.parent.lookup(name)


	def __str__(self):
		return str(self.node.name)
