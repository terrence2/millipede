'''
Copyright (c) 2011, Terrence Cole.
All rights reserved.
'''


class MelanoFunction:
	def __init__(self, node):
		self.node = node
		self.parent = None
		self.names = {}


	def __str__(self):
		return str(self.node.name)
