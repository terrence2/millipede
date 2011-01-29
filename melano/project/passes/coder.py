'''
Copyright (c) 2011, Terrence Cole.
All rights reserved.
'''
from contextlib import contextmanager
from melano.parser import ast
from melano.parser.visitor import ASTVisitor


class Coder(ASTVisitor):
	'''
	Use the type information to lay out low-level code (or high-level code as needed).
	'''
	def __init__(self, project, module, target):
		self.project = project
		self.module = module
		self.target = target
		self.context = None


	@contextmanager
	def scope(self, ctx):
		prior = self.context
		self.context = ctx
		yield
		self.context = prior


	def visit_Module(self, node):
		self.context = self.target.create_module_function()
		self.visit_nodelist(node.body)


	def visit_Attribute(self, node):
		if node.ctx == ast.Store:
			varname = self.context.get_variable_name(str(node).replace('.', '_'))
			self.context.add_variable(node.hl.get_type().name(), varname)
			node.hl.name = varname


	def visit_Name(self, node):
		if node.ctx == ast.Store:
			varname = self.context.get_variable_name(node.id)
			self.context.add_variable(node.hl.get_type().name(), varname)
			node.hl.name = varname


	def visit_FunctionDef(self, node):
		ctx = self.target.create_function(str(node.name))
		with self.scope(ctx):
			self.visit_nodelist(node.body)


	def visit_Import(self, node):
		for alias in node.names:
			self.visit(alias.name)
			self.visit(alias.asname)
			return

			# Note: exposing a name can take one of two paths, either importing an existing LL definition from another
			#		LL source, making it directly available, or we need to perform a pythonic import to get the names
			mod = self.project.find_module(str(alias.name), self.module)
			if self.project.is_local(mod):
				raise NotImplementedError
				self.target.import_local(str(alias.name))
			else:
				#self.context.import_python(str(alias.name))
				print('IMP:', alias.name.hl.name)

	"""

	#def visit_ImportFrom(self, node):
	#	#import pdb;pdb.set_trace()
	#	self.context.import_from(node.level, str(node.module), [str(n) for n in node.names])


	def visit_If(self, node):
		self.visit(node.test)
		print(node.test.hl.name)
		#ctx = self.context.create_if():
		#with self.scope(ctx):
		#	self.visit_nodelist(nodes)


	def visit_Compare(self, node):
		self.visit(node.left)


	def visit_Attribute(self, node):
		self.visit(node.value)


	def visit_Assign(self, node):
		for tgt in node.targets:
			self.context.add_variable(tgt.hl.type(), str(tgt))
		import pdb; pdb.set_trace()


	def visit_If(self, node):
		with self.scope(self.context.if_stmt()):
			self.visit(node.test)
		with self.scope(self.context.block()):
			self.visit_nodelist(node.body)
		if node.orelse:
			self.context.else_stmt()
			with self.scope(self.context.block()):
				self.visit_nodelist(node.orelse)
	"""
