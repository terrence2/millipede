'''
Copyright (c) 2011, Terrence Cole.
All rights reserved.
'''

class AST:
	'''Base class of all ast nodes.'''
	_fields = ()
	__slots__ = ('symbol', 'hl', 'bb', 'bb_else', 'start', 'end') #'llnode')
	def __init__(self, llnode):

		# FIXME: push these down to block that actually use them?
		self.bb = self.bb_else = None

		#self.llnode = None
		self.hl = None
		self.symbol = None
		if llnode:
			self.start = llnode.startpos
			self.end = llnode.endpos
		else:
			self.start = self.end = None

	def llcopy(self, other):
		'''Take low-level parameters from the other node.'''
		#self.llnode = other.llnode
		self.start = other.start
		self.end = other.end

	def __repr__(self):
		return '<' + self.__class__.__name__ + '>'

	#@property
	#def start(self):
	#	return self.llnode.startpos

	#@property
	#def end(self):
	#	return self.llnode.endpos

