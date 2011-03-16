'''
Copyright (c) 2011, Terrence Cole.
All rights reserved.
'''
from . import ast as c
from contextlib import contextmanager
from melano.c.ast import CPP, FuncDef
from melano.lang.visitor import ASTVisitor


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

	def visit_ArrayDecl(self, node):
		self.visit(node.type)

	def visit_ArrayRef(self, node):
		self.visit(node.name)
		self.fp.write('[')
		self.visit(node.subscript)
		self.fp.write(']')
		#self.fp.write(str(node.name) + '[' + str(node.subscript) + ']')

	def visit_Assignment(self, node):
		self.visit(node.lvalue)
		self.fp.write(' ' + node.op + ' ')
		self.visit(node.rvalue)

	def visit_BinaryOp(self, node):
		self.visit(node.left)
		self.fp.write(' ' + node.op + ' ')
		self.visit(node.right)

	def visit_Break(self, node):
		self.fp.write('break')

	def visit_Cast(self, node):
		self.fp.write('(')
		self.visit(node.to_type)
		self.fp.write(')')
		self.visit(node.expr)

	def visit_Comment(self, node):
		self.fp.write('/* ' + node.value + ' */')

	def visit_Compound(self, node):
		self.fp.write(' {\n')
		with self.tab():
			for item in node.block_items:
				# labels are dedented by one line, compared to other elements
				if not isinstance(item, c.Label):
					self.fp.write(self.level * '\t')
				else:
					self.fp.write(max(0, self.level - 1) * '\t')

				self.visit(item)

				# not all elements require a closing ; 
				if not isinstance(item, (c.Comment, c.Compound, c.For, c.If, c.Label, c.Switch, c.While)):
					self.fp.write(';')
				self.fp.write('\n')
		self.fp.write(self.level * '\t' + '}')

	def visit_Constant(self, node):
		if node.type == 'string':
			self.fp.write(node.prefix + '"' + node.value + '"' + node.postfix)
		elif node.type == 'integer':
			self.fp.write(node.prefix + str(node.value) + node.postfix)
		elif node.type == 'double':
			self.fp.write(node.prefix + repr(node.value).strip("'") + node.postfix)
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
		elif isinstance(node.type, c.ArrayDecl):
			self.fp.write('[' + str(node.type.dim) + ']')
		if node.bitsize:
			self.fp.write(': ' + str(node.bitsize))
		if node.init:
			self.fp.write(' = ')
			if isinstance(node.init, c.ExprList):
				self.fp.write('{')
				self.visit(node.init)
				self.fp.write('}')
			else:
				self.visit(node.init)

	def visit_DoWhile(self, node):
		self.fp.write('do')
		self.visit(node.stmt)
		self.fp.write(' while(')
		self.visit(node.cond)
		self.fp.write(')')

	def visit_ExprList(self, node):
		if not len(node.exprs): return
		for exp in node.exprs[:-1]:
			self.visit(exp)
			self.fp.write(', ')
		self.visit(node.exprs[-1])

	def visit_For(self, node):
		self.fp.write('for(')
		self.visit(node.init)
		self.fp.write('; ')
		self.visit(node.cond)
		self.fp.write('; ')
		self.visit(node.next)
		self.fp.write(')')
		self.visit(node.stmt)

	def visit_FuncCall(self, node):
		self.visit(node.name)
		self.fp.write('(')
		self.visit(node.args)
		self.fp.write(')')

	def visit_FuncDef(self, node):
		self.visit(node.decl)
		self.visit(node.body)

	def visit_Goto(self, node):
		# Note: computed goto's need to visit the name
		if isinstance(node.name, c.AST):
			self.fp.write('goto ')
			self.visit(node.name)
		else:
			self.fp.write('goto ' + node.name)

	def visit_ID(self, node):
		self.fp.write(node.name)

	def visit_IdentifierType(self, node):
		self.fp.write(' '.join(node.names))

	def visit_If(self, node):
		self.fp.write('if(')
		if isinstance(node.cond, c.Assignment):
			self.fp.write('(')
			self.visit(node.cond)
			self.fp.write(')')
		else:
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

	def visit_Label(self, node):
		self.fp.write(node.name + ':')
		self.visit(node.stmt)

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

	def visit_Struct(self, node):
		self.fp.write('struct ' + node.name)
		if node.decls:
			self.fp.write('{')
			for n in node.decls:
				self.visit(n)
				self.fp.write(';')
			self.fp.write('}')

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

	def visit_While(self, node):
		self.fp.write('while(')
		if isinstance(node.cond, c.Assignment):
			self.fp.write('(')
			self.visit(node.cond)
			self.fp.write(')')
		else:
			self.visit(node.cond)
		self.fp.write(')')
		self.visit(node.stmt)
