'''
Walk an AST.  Copied and extended from CPython.
'''
from collections import Iterable
from .ast import AST


class ASTVisitor:
	def __init__(self):
		# track current context node to give output methods access to our state for printing errors
		self._current_node = None


	def visit(self, node):
		"""Visit a node."""
		self._current_node = node
		if node is None: return
		method = 'visit_' + node.__class__.__name__
		visitor = getattr(self, method, self.generic_visit)
		return visitor(node)


	def generic_visit(self, node):
		"""Called if no explicit visitor function exists for a node."""
		rv = None
		for value in [getattr(node, f) for f in node._fields]:
			if isinstance(value, Iterable):
				for item in value:
					if isinstance(item, AST):
						rv = self.visit(item)
			elif isinstance(value, AST):
				rv = self.visit(value)
		return rv


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
