'''
Copyright (c) 2011, Terrence Cole.
All rights reserved.
'''
from contextlib import contextmanager
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


	def name(self, *args):
		return '_'.join((self.project.name, self.module.names['__name__']) + args)


	@contextmanager
	def scope(self, ctx):
		prior = self.context
		self.context = ctx
		yield
		self.context = prior


	def visit_Module(self, node):
		entryname = self.name()
		self.context = self.target.create_module_function(entryname)
		self.visit_nodelist(node.body)


	def visit_FunctionDef(self, node):
		ctx = self.target.create_function(self.name(str(node.name)))
		with self.scope(ctx):
			self.visit_nodelist(node.body)


	def visit_Assign(self, node):
		pass
		#for tgt in node.targets:
		#	self.context.add_variable(tgt.hl.type(), str(tgt))
		#import pdb; pdb.set_trace()

	"""
	def visit_If(self, node):
		with self.scope(self.context.if_stmt()):
			self.visit(node.test)
		with self.scope(self.context.block()):
			self.visit_nodelist(node.body)
		if node.orelse:
			self.context.else_stmt()
			with self.scope(self.context.block()):
				self.visit_nodelist(node.orelse)


	def visit_Compare(self, node):
		import pdb; pdb.set_trace()
	"""
