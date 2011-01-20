'''
Copyright (c) 2011, Terrence Cole.
All rights reserved.
'''

class MelanoVariable:
	def __init__(self, node, owner):
		self.node = node
		self.owner = None
		self.types = []

		# backref, so visitors can find us
		self.node.hl = self


	def __str__(self):
		return str(self.node)
