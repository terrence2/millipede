'''
Walk an AST.  Copied and extended from CPython.
'''
from collections import Iterable
from .ast import AST


class ASTVisitor:
	def __init__(self):
		# track current context node to give output methods access to our state for printing errors
		self._current_node = None
		self._current_line = 0


	def on_line_changed(self, lineno):
		'''Called every time the line number of the currently visited node changes.'''


	def _v_inner(self, node):
		'''Note move lookup to subnode to improve the most common traceback and tracing tasks.'''
		if node is None:
			return lambda node: None

		# check for line changes
		if node.start:
			ln = node.start[0]
			if ln != self._current_line:
				self._current_line = ln
				self.on_line_changed(ln)

		# lookup the method
		self._current_node = node
		method = 'visit_' + node.__class__.__name__
		visitor = getattr(self, method, self.generic_visit)
		return visitor


	def visit(self, node):
		"""Visit a node."""
		v = self._v_inner(node)
		return v(node)


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
