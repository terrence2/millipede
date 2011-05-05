'''
Copyright (c) 2011, Terrence Cole.
All rights reserved.
'''

class Nonable:
	def __init__(self, ty):
		self.ty = ty
Opt = Nonable

class Choice:
	def __init__(self, *tys):
		self.tys = tys
