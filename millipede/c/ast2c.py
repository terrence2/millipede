'''
Copyright (c) 2011, Terrence Cole.
All rights reserved.
'''
from millipede.lang.visitor import ASTVisitor


class Ast2C(ASTVisitor):
	'''Convert the ast to c by walking the tree and working with the basic blocks at the lowest level.'''

	def __init__(self, project):
		self.project = project


	def visit_Module(self, node):
		super.generic_visit(node)

		for op in node.bb:
			v = getattr(self, 'visit_' + node.__class__.__name__, None)
			if v:
				return v(op)

