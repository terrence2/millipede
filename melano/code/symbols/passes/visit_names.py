'''
Extract symbols from an AST
'''
__author__ = 'Terrence Cole <terrence@zettabytestorage.com>'

from contextlib import contextmanager
from melano.code.symbols.block import Block
from melano.code.symbols.class_ import Class
from melano.code.symbols.function import Function
from melano.code.symbols.module import Module
from melano.code.symbols.name import Name
from melano.parser.common.visitor import ASTVisitor
import melano.parser.py3.ast as ast


class NameExtractor(ASTVisitor):
	def __init__(self, module:Module):
		super().__init__()

		# the symbol database we will be writing to
		self.module = module
		self._context = [module]


	@property
	def context(self):
		return self._context[-1]


	@contextmanager
	def location(self, location:Block):
		self._context.append(location)
		yield
		self._context.pop()


	def visit_Module(self, node):
		for stmt in node.body:
			self.visit(stmt)


	def visit_ImportFrom(self, node):
		for alias in node.names:
			if alias.asname:
				self.context.add_symbol(Name(alias.asname))
			else:
				self.context.add_symbol(Name(alias.name))

			#	name = alias.name
			#	while isinstance(name, ast.Attribute):
			#		name = name.value
			#	self.db.insert(self.name(name.id), ast)


	def visit_Import(self, node):
		for alias in node.names:
			if alias.asname:
				self.context.add_symbol(Name(alias.asname))
			else:
				self.context.add_symbol(Name(alias.name))
			#if alias.asname:
			#	self.db.insert(self.name(alias.asname.id), ast)
			#else:
			#	name = alias.name
			#	while isinstance(name, ast.Attribute):
			#		name = name.value
			#	self.db.insert(self.name(name.id), ast)


	def visit_FunctionDef(self, node):
		fn = Function(node.name.id, node)
		self.context.add_symbol(fn)

		with self.location(fn):
			# visit arg definitions
			if node.args.args:
				for arg in node.args.args:
					self.context.add_symbol(Name(arg.arg))
			if node.args.vararg:
				self.context.add_symbol(Name(node.args.vararg))
			if node.args.kwonlyargs:
				for arg in node.args.kwonlyargs:
					self.context.add_symbol(Name(arg.arg))
			if node.args.kwarg:
				self.context.add_symbol(Name(node.args.kwarg))

			# visit children
			for stmt in node.body:
				#print("VISIT:", stmt)
				self.visit(stmt)

		'''
		# annotations and defaults are evaluated in enclosing context
		if node.returns:
			self.visit(node.returns)
		if node.args.args:
			for arg in node.args.args:
				if arg.annotation:
					self.visit(arg.annotation)
		if node.args.varargannotation:
			self.visit(node.args.varargannotation)
		if node.args.kwonlyargs:
			for arg in node.args.kwonlyargs:
				if arg.annotation:
					self.visit(arg.annotation)
		if node.args.kwargannotation:
			self.visit(node.args.kwargannotation)
		if node.args.defaults:
			for expr in node.args.defaults:
				self.visit(expr)
		if node.args.kw_defaults:
			for expr in node.args.kw_defaults:
				self.visit(expr)

		

		# decorators are visited in enclosing level, after evaluating sub-level
		if node.decorator_list:
			for deco in node.decorator_list:
				self.visit(deco)
			
		# bind the function name into the enclosing scope after definition
		with self.location('functiondef'):
			self.scope.bind(node.name, func_scope)
		'''


	def visit_Name(self, node):
		if node.ctx == ast.Store:
			self.context.add_symbol(Name(node))