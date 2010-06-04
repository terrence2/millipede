'''
Construct a block syntax tree from an ast.
'''
__author__ = 'Terrence Cole <terrence@zettabytestorage.com>'

from melano.parser.common.visitor import ASTVisitor
from .nodes import ModuleBlock, FunctionBlock, ClassBlock


class BSTBuilder(ASTVisitor):
	def __init__(self):
		self.bst = None
		self.context = None


	def visit_Module(self, node):
		assert self.bst is None
		self.bst = ModuleBlock(node)
		self.context = self.bst
		
		for stmt in node.body:
			self.visit(stmt)


	def visit_Import(self, node):
		self.bst.all_imports.append(node)
		if hasattr(self.context, 'imports'):
			self.context.imports.append(node)


	def visit_ImportFrom(self, node):
		self.bst.all_imports.append(node)
		if hasattr(self.context, 'imports'):
			self.context.imports.append(node)


	def visit_ClassDef(self, node):
		class_block = ClassBlock(node)
		self.bst.all_classes.append(class_block)
		if hasattr(self.context, 'classes'):
			self.context.classes.append(class_block)
		
		prior = self.context
		self.context = class_block
		
		for stmt in node.body:
			self.visit(stmt)
		
		self.context = prior


	def visit_FunctionDef(self, node):
		func_block = FunctionBlock(node)
		if isinstance(self.context, ClassBlock):
			self.context.methods.append(func_block)
			self.bst.all_methods.append(func_block)
		else:
			if hasattr(self.context, 'functions'):
				self.context.functions.append(func_block)
			self.bst.all_functions.append(func_block)
		
		prior = self.context
		self.context = func_block
		
		for stmt in node.body:
			self.visit(stmt)
		
		self.context = prior


	def visit_Return(self, node):
		if hasattr(self.context, 'returns'):
			self.context.returns.append(node)


	def visit_Raise(self, node):
		if hasattr(self.context, 'raises'):
			self.context.raises.append(node)


	def visit_Yield(self, node):
		if hasattr(self.context, 'yields'):
			self.context.yields.append(node)

