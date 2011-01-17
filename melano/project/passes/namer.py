'''
Copyright (c) 2011, Terrence Cole.
All rights reserved.
'''
from contextlib import contextmanager
from melano.parser.visitor import ASTVisitor
from melano.project.class_ import MelanoClass


class Namer(ASTVisitor):
	'''Get the names of things in this module.'''

	def __init__(self, module):
		super().__init__()
		self.module = module
		self.context = self.module


	@contextmanager
	def scope(self, node):
		# insert node into parent scope
		self.context.names[str(node)] = node

		# push a new scope
		prior = node.parent = self.context
		self.context = node
		yield
		self.context = prior


	def visit_ClassDef(self, node):
		with self.scope(MelanoClass(node)):
			for stmt in node.body:
				self.generic_visit(stmt)
		for stmt in node.decorator_list:
			self.generic_visit(stmt)


	def visit_Method(self, node):
		print("METHOD:", node)


	def visit_FunctionDef(self, node):
		#with self.scope(str(node.name)) as name:
		#	self.module.names[name] = node
		print("FUNCTION:", node)

