'''
Copyright (c) 2011, Terrence Cole.
All rights reserved.
'''
from millipede.lang.visitor import ASTVisitor

class NodePositionMapper(ASTVisitor):
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.out = []

	def visit(self, node):
		super().visit(node)
		self.out.append((node.start, node.end, node.hl))
