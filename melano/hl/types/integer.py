'''
Copyright (c) 2011, Terrence Cole.
All rights reserved.
'''
from melano.hl.types.hltype import HLType


class CIntegerType(HLType):
	def __init__(self, size=None, signed=None, is_a_bool=False):
		super().__init__()
		self.size = size
		self.signed = signed
		# allow us to use ints as bools at the C level and still get the right promotion to pyobject later
		self.is_a_bool = is_a_bool

