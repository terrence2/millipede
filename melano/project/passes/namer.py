'''
Copyright (c) 2011, Terrence Cole.
All rights reserved.
'''
from contextlib import contextmanager
from melano.parser.visitor import ASTVisitor
from melano.project.class_ import MelanoClass
from melano.project.function import MelanoFunction


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
		self.visit_nodelist(node.bases)
		self.visit_nodelist(node.keywords)
		if node.starargs:
			self.visit(node.starargs)
		if node.kwargs:
			self.visit(node.kwargs)
		with self.scope(MelanoClass(node)):
			self.visit_nodelist(node.body)
		self.visit_nodelist(node.decorator_list)


	def visit_Method(self, node):
		print("METHOD:", node)


	def visit_FunctionDef(self, node):
		print("FUNCTION:", node)
		with self.scope(MelanoFunction(node)):
			import pdb; pdb.set_trace()

