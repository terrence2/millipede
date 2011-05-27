'''
Copyright (c) 2011, Terrence Cole.
All rights reserved.
'''
from millipede.lang.visitor import ASTVisitor


class FindLinks(ASTVisitor):
	def __init__(self):
		super().__init__()
		self.imports = []
		self.importfroms = []
		self.renames = {}


	def visit_Import(self, node):
		for alias in node.names:
			v = str(alias.name)
			if alias.asname:
				k = str(alias.asname)
				if k not in self.renames: self.renames[k] = []
				if v not in self.renames[k]: self.renames[k].append(v)
			self.imports.append(v)


	def visit_ImportFrom(self, node):
		names = []
		for alias in node.names:
			v = str(alias.name)
			if alias.asname:
				k = str(alias.asname)
				if k not in self.renames: self.renames[k] = []
				if v not in self.renames[k]: self.renames[k].append(v)
			names.append(v)
		self.importfroms.append((node.level, node.module, names))
