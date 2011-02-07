'''
Copyright (c) 2011, Terrence Cole.
All rights reserved.
'''
from . import ast as c
from contextlib import contextmanager
from melano.c.ast import CPP, FuncDef
from melano.parser.visitor import ASTVisitor


class COut(ASTVisitor):
	def __init__(self, filename):
		super().__init__()
		self.filename = filename
		self.level = 0

	def __enter__(self):
		self.fp = open(self.filename, 'w')
		return self

	def __exit__(self, *args):
		self.fp.close()
		self.fp = None

	@contextmanager
	def tab(self):
		self.level += 1
		yield
		self.level -= 1

	def visit_Assignment(self, node):
		self.visit(node.lvalue)
		self.fp.write(' ' + node.op + ' ')
		self.visit(node.rvalue)

	def visit_BinaryOp(self, node):
		self.visit(node.left)
		self.fp.write(' ' + node.op + ' ')
		self.visit(node.right)

	def visit_Comment(self, node):
		self.fp.write('/* ' + node.value + ' */')

	def visit_Compound(self, node):
		self.fp.write(' {\n')
		with self.tab():
			for item in node.block_items:
				self.fp.write(self.level * '\t')
				self.visit(item)
				self.fp.write(';\n')
		self.fp.write(self.level * '\t' + '}')

	def visit_Constant(self, node):
		if node.type == 'string':
			self.fp.write('"' + node.value + '"')
		elif node.type == 'integer':
			self.fp.write(str(node.value))
		else:
			raise NotImplementedError

	def visit_Decl(self, node):
		q = ' '.join(node.quals + node.storage + node.funcspec)
		if q: self.fp.write(q + ' ')
		if isinstance(node.type, c.FuncDecl):
			self.visit(node.type.type)
		else:
			self.visit(node.type)
		self.fp.write(' ' + node.name)
		if isinstance(node.type, c.FuncDecl):
			self.fp.write('(')
			self.visit(node.type.args)
			self.fp.write(')')
		if node.bitsize:
			self.fp.write(': ' + str(node.bitsize))
		if node.init:
			self.fp.write(' = ')
			self.visit(node.init)

	def visit_ExprList(self, node):
		if not len(node.exprs): return
		for exp in node.exprs[:-1]:
			self.visit(exp)
			self.fp.write(', ')
		self.visit(node.exprs[-1])

	def visit_ID(self, node):
		self.fp.write(node.name)

	def visit_IdentifierType(self, node):
		self.fp.write(' '.join(node.names))

	def visit_If(self, node):
		self.fp.write('if(')
		self.visit(node.cond)
		self.fp.write(')')
		self.visit(node.iftrue)
		if(node.iffalse):
			self.fp.write(' else ')
			self.visit(node.iffalse)

	def visit_Include(self, node):
		if node.is_system:
			self.fp.write('#include <{}>'.format(node.name))
		else:
			self.fp.write('#include "{}"'.format(node.name))

	def visit_FuncCall(self, node):
		self.visit(node.name)
		self.fp.write('(')
		self.visit(node.args)
		self.fp.write(')')

	def visit_FuncDef(self, node):
		self.visit(node.decl)
		self.visit(node.body)

	def visit_ParamList(self, node):
		if not len(node.params): return
		for p in node.params[:-1]:
			self.visit(p)
			self.fp.write(', ')
		self.visit(node.params[-1])

	def visit_PtrDecl(self, node):
		self.visit(node.type)
		q = ' '.join(node.quals)
		if q: q = ' ' + q + ' '
		self.fp.write('*' + q)

	def visit_Return(self, node):
		self.fp.write('return ');
		self.visit(node.expr)

	def visit_TranslationUnit(self, node):
		for n in node.ext:
			self.visit(n)
			if not isinstance(n, (CPP, FuncDef)):
				self.fp.write(';')
			self.fp.write('\n')

	def visit_TypeDecl(self, node):
		q = ' '.join(node.quals)
		if q: self.fp.write(q + ' ')
		self.visit(node.type)
		#self.fp.write(' ' + node.declname)

	def visit_UnaryOp(self, node):
		self.fp.write(node.op)
		self.visit(node.expr)