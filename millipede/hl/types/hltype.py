'''
Copyright (c) 2011, Terrence Cole.
All rights reserved.
'''

class HLType:
	def __eq__(self, other):
		'''Types are equal if they have the same class.'''
		return self.__class__ == other.__class__


