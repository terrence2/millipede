'''
Copyright (c) 2011, Terrence Cole.
All rights reserved.
'''
from millipede.lang.visitor import ASTVisitor


class Clean(ASTVisitor):
	def visit(self, node):
		if node.hl:
			node.hl.ll = None
		super().visit(node)
