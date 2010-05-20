

class AST:
	'''Base class of all ast nodes.'''

	__slots__ = ('startpos', 'endpos')
	def __init__(self, node):
		self.startpos = node.startpos
		self.endpos = node.endpos

