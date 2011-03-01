'''
Copyright (c) 2011, Terrence Cole.
All rights reserved.
'''
from melano.hl.coerce import Coerce
from melano.lang.visitor import ASTVisitor
import pdb


class Typer(ASTVisitor):
	def __init__(self, project, module):
		self.project = project
		self.module = module


	def visit_Assign(self, node):
		self.visit(node.value)
		for target in node.targets:
			self.visit(target)
			if node.value.hl:
				target.hl.add_type(node.value.hl.get_type())


	'''
	def visit_Call(self, node):
		#print(dir(node))
		#import pdb; pdb.set_trace()
		self.visit_nodelist(node.args)
		self.visit_nodelist(node.keywords)
		self.visit(node.starargs)
		self.visit(node.kwargs)
		self.visit(node.func)
		# Check parameter types against annotation types.
		# Annotate parameters (in callee) with type of args/annotations.
		# Note type of annotated return as the type of the call.
		node.hl = node.func.hl
	'''


	def visit_BinOp(self, node):
		self.visit(node.left)
		self.visit(node.right)
		node.hl = Coerce(Coerce.GENERALIZE, node.left.hl, node.right.hl)

	def visit_UnaryOp(self, node):
		self.visit(node.operand)
		node.hl = node.operand.hl

