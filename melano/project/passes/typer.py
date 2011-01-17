'''
Copyright (c) 2011, Terrence Cole.
All rights reserved.
'''
from melano.parser.common.visitor import ASTVisitor

class Typer(ASTVisitor):
	def visit_Assign(self, node):
		import pdb; pdb.set_trace()
