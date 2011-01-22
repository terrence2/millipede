'''
Copyright (c) 2011, Terrence Cole.
All rights reserved.
'''

class MelanoConst:
	def __init__(self, ty:type, value:object):
		self.type = ty
		self.value = value

	def __str__(self):
		return '<Const[{}]>'.format(str(self.value))
