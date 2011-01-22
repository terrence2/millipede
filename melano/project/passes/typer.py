'''
Copyright (c) 2011, Terrence Cole.
All rights reserved.
'''
from melano.parser.visitor import ASTVisitor
from melano.project.foreign import ForeignObject
from melano.project.type.object import PyObject

class Typer(ASTVisitor):
	def __init__(self, project, module):
		self.project = project
		self.module = module


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


	def visit_Assign(self, node):
		self.visit_nodelist(node.targets)
		self.visit(node.value)

		import pdb; pdb.set_trace()
		for tgt in node.targets:
			tgt.hl.types.extend(node.value.hl.types)

