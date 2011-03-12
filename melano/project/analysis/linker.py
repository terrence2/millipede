'''
Copyright (c) 2011, Terrence Cole.
All rights reserved.
'''
from contextlib import contextmanager
from melano.py import ast as py
from melano.lang.visitor import ASTVisitor
from melano.hl.module import MelanoModule
from melano.hl.nameref import NameRef
import pdb


class Linker(ASTVisitor):
	'''
	Lookup all referenced names and attach them into the namespace/variable names as needed.
	'''

	def __init__(self, project, module):
		super().__init__()
		self.project = project
		self.module = module
		self.context = self.module


	@contextmanager
	def scope(self, ctx):
		# push a new scope
		prior = self.context
		self.context = ctx
		yield
		self.context = prior


	def visit_ClassDef(self, node):
		self.visit(node.name)
		self.visit_nodelist(node.bases)
		self.visit_nodelist(node.keywords)
		self.visit(node.starargs)
		self.visit(node.kwargs)
		with self.scope(node.hl):
			self.visit_nodelist(node.body)
		self.visit_nodelist(node.decorator_list)


	def visit_FunctionDef(self, node):
		self.visit(node.returns) # return annotation
		self.visit_nodelist_field(node.args.args, 'annotation') # position arg annotations
		self.visit(node.args.varargannotation) # *args annotation
		self.visit_nodelist_field(node.args.kwonlyargs, 'annotation') # kwargs annotation
		self.visit(node.args.kwargannotation) # **args annotation
		self.visit_nodelist(node.args.defaults) # positional arg default values
		self.visit_nodelist(node.args.kw_defaults) # kwargs default values

		with self.scope(node.hl):
			# arg name defs are inside the func
			self.visit_nodelist_field(node.args.args, 'arg')
			self.visit(node.args.vararg)
			self.visit_nodelist_field(node.args.kwonlyargs, 'arg')
			self.visit(node.args.kwarg)

			self.visit_nodelist(node.body)

		self.visit_nodelist(node.decorator_list)


	def visit_Import(self, node):
		for alias in node.names:
			if alias.asname:
				self.visit(alias.asname)
			else:
				if isinstance(alias.name, py.Attribute):
					self.visit(alias.name.first())
				else:
					self.visit(alias.name)

	def visit_ImportFrom(self, node):
		'''Note: we need to already be indexed to provide names for * imports, so we _also_
			do import_from in link.'''
		modname = '.' * node.level + str(node.module)
		mod = self.module.refs.get(modname, None)
		if not mod:
			raise NotImplementedError('No ref to module {} when linking'.format(modname))

		for alias in node.names:
			assert not isinstance(alias.name, py.Attribute)
			if alias.asname:
				self.visit(alias.asname)
			else:
				if str(alias.name) == '*':
					for n, ref in mod.lookup_star().items():
						self.context.add_symbol(n)
				else:
					self.visit(alias.name)


	def visit_Name(self, node):
		if node.ctx == py.Load:
			sym = self.context.lookup(str(node))
			ref = self.context.add_reference(sym)
			node.hl = ref


	def visit_TryExcept(self, node):
		self.visit_nodelist(node.body)
		# do lookup on exception type's here
		for handler in node.handlers:
			if handler.type:
				sym = self.context.lookup(str(handler.type))
				ref = self.context.add_reference(sym)
				handler.type.hl = ref
			else:
				assert handler is node.handlers[-1], "default 'except' must be last"
			# NOTE: don't bother visiting the name, since we know it is a Store
			self.visit_nodelist(handler.body)
