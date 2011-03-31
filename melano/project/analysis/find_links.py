'''
Copyright (c) 2011, Terrence Cole.
All rights reserved.
'''
from melano.lang.visitor import ASTVisitor


class FindLinks(ASTVisitor):
	def __init__(self):
		self.imports = []
		self.importfroms = []
		self.ref_paths = {}
		self.renames = {}

	def visit_Import(self, node):
		self.imports.append(node)
		for alias in node.names:
			if alias.asname:
				k = str(alias.asname)
				v = str(alias.name)
				if k not in self.renames: self.renames[k] = []
				if v not in self.renames[k]: self.renames[k].append(v)

	def visit_ImportFrom(self, node):
		self.importfroms.append(node)
		for alias in node.names:
			if alias.asname:
				k = str(alias.asname)
				v = str(alias.name)
				if k not in self.renames: self.renames[k] = []
				if v not in self.renames[k]: self.renames[k].append(v)
