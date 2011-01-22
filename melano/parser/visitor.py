'''
Walk an AST.  Copied and extended from CPython.
'''
from .ast import AST


def iter_fields(node):
	"""
	Yield a tuple of ``(fieldname, value)`` for each field in ``node._fields``
	that is present on *node*.
	"""
	for field in node._fields:
		try:
			yield field, getattr(node, field)
		except AttributeError:
			print("No attribute: {} on {}".format(field, node.__class__.__name__))



class ASTVisitor:
	def visit(self, node):
		"""Visit a node."""
		if node is None: return
		method = 'visit_' + node.__class__.__name__
		visitor = getattr(self, method, self.generic_visit)
		return visitor(node)


	def generic_visit(self, node):
		"""Called if no explicit visitor function exists for a node."""
		for field, value in iter_fields(node):
			if isinstance(value, list):
				for item in value:
					if isinstance(item, AST):
						self.visit(item)
			elif isinstance(value, AST):
				self.visit(value)


	def visit_nodelist(self, nodes):
		"""Visit all nodes in the given list."""
		if nodes is None: return
		for node in nodes:
			self.visit(node)


	def visit_nodelist_field(self, nodes, field):
		if nodes is None: return
		for node in nodes:
			val = getattr(node, field, None)
			self.visit(val)
