'''
Copyright (c) 2011, Terrence Cole.
All rights reserved.
'''
from melano.parser.visitor import ASTVisitor


class FindLinks(ASTVisitor):
	def __init__(self):
		self.imports = []
		self.importfroms = []

	def visit_Import(self, node):
		self.imports.append(node)

	def visit_ImportFrom(self, node):
		self.importfroms.append(node)
