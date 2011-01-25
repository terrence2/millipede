'''
Copyright (c) 2011, Terrence Cole.
All rights reserved.
'''
from melano.project.lowlevel.if_stmt import LLIf

class LLElse:
	def emit(self, fp, pad):
		fp.write(pad + 'else')


class LLBlock:
	'''Collection of statements in {}'''

	def __init__(self):
		self.vars = []
		self.stmts = []


	def import_from(self, level:int, module:str, names:[str]):
		pass


	def add_variable(self, ty, name):
		self.vars.append((ty, name))


	def if_stmt(self):
		s = LLIf()
		self.stmts.append(s)
		return s


	def else_stmt(self):
		s = LLElse()
		self.stmts.append(s)
		return s


	def block(self):
		b = LLBlock()
		self.stmts.append(b)
		return b


	def emit(self, fp, pad):
		fp.write(pad + '{\n')
		for stmt in self.stmts:
			stmt.emit(fp, pad + '\t')
			fp.write('\n')
		fp.write(pad + '}\n')
