'''
Copyright (c) 2011, Terrence Cole.
All rights reserved.
'''
from millipede.hl.nodes.entity import Entity
from millipede.hl.types.hltype import HLType


class Constant(Entity):
	'''Holds a type list of one element.  It is here to be ref'd by Names so that constants in the tree can propogate thier types.'''
	def __init__(self, ty:HLType, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.add_type(ty)

