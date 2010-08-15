'''
A namespace with runnable code.
'''
__author__ = 'Terrence Cole <terrence@zettabytestorage.com>'

from .namespace import Namespace


class Block(Namespace):
	'''A chunk of python code that belongs to a single frame.  Where the frame
		represents the active values of the interpretter state, the block
		contains the lexical scoping information.
	'''
	def __init__(self, name, node, *args, **kwargs):
		super().__init__(name, *args, **kwargs)
		self.node = node

