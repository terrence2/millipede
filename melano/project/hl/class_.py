'''
Copyright (c) 2011, Terrence Cole.
All rights reserved.
'''

class MelanoClass:
	def __init__(self, node):
		self.node = node
		self.parent = None
		self.names = {}

		# backref, so visitors can find us
		self.node.hl = self


	def __str__(self):
		return str(self.node.name)
