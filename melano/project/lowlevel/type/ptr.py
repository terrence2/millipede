'''
Copyright (c) 2011, Terrence Cole.
All rights reserved.
'''

class Ptr:
	def __init__(self, subtype):
		self.ty = subtype


	def name(self):
		return self.ty.name() + '*'
