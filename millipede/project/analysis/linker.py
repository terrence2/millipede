'''
Copyright (c) 2011, Terrence Cole.
All rights reserved.
'''
from contextlib import contextmanager
from millipede.hl.nodes.attribute import Attribute
from millipede.hl.nodes.call import Call
from millipede.hl.nodes.coerce import Coerce
from millipede.hl.nodes.entity import Entity
from millipede.hl.nodes.name import Name
from millipede.hl.nodes.nameref import NameRef
from millipede.hl.nodes.subscript import Subscript
from millipede.lang.visitor import ASTVisitor
from millipede.py import ast as py
import pdb


class Linker(ASTVisitor):
	'''
	Lookup all referenced names and attach them into the namespace/variable names as needed.
	'''

	def __init__(self, project, module):
		super().__init__()
		self.project = project
		self.module = module
		self.scope = self.module


	@contextmanager
	def push_scope(self, ctx):
		# push a new scope
		prior = self.scope
		self.scope = ctx
		yield
		self.scope = prior


	def visit_ClassDef(self, node):
		self.visit(node.name)
		self.visit_nodelist(node.bases)
		self.visit_nodelist(node.keywords)
		self.visit(node.starargs)
		self.visit(node.kwargs)
		with self.push_scope(node.hl):
			self.visit_nodelist(node.body)
		self.visit_nodelist(node.decorator_list)


	def visit_DictComp(self, node):
		with self.push_scope(node.hl):
			self.visit_nodelist(node.generators)
			self.visit(node.key)
			self.visit(node.value)


	def visit_FunctionDef(self, node):
		self.visit(node.returns) # return annotation
		self.visit_nodelist_field(node.args.args, 'annotation') # position arg annotations
		self.visit(node.args.varargannotation) # *args annotation
		self.visit_nodelist_field(node.args.kwonlyargs, 'annotation') # kwargs annotation
		self.visit(node.args.kwargannotation) # **args annotation
		self.visit_nodelist(node.args.defaults) # positional arg default values
		self.visit_nodelist(node.args.kw_defaults) # kwargs default values

		with self.push_scope(node.hl):
			# arg name defs are inside the func
			self.visit_nodelist_field(node.args.args, 'arg')
			self.visit(node.args.vararg)
			self.visit_nodelist_field(node.args.kwonlyargs, 'arg')
			self.visit(node.args.kwarg)

			self.visit_nodelist(node.body)

		self.visit_nodelist(node.decorator_list)


	def visit_GeneratorExp(self, node):
		with self.push_scope(node.hl):
			self.visit_nodelist(node.generators)
			self.visit(node.elt)


	def visit_Lambda(self, node):
		self.visit_nodelist(node.args.defaults) # positional arg default values
		self.visit_nodelist(node.args.kw_defaults) # kwargs default values
		with self.push_scope(node.hl):
			self.visit_nodelist_field(node.args.args, 'arg')
			self.visit(node.args.vararg)
			self.visit_nodelist_field(node.args.kwonlyargs, 'arg')
			self.visit(node.args.kwarg)
			self.visit_nodelist(node.body)


	def visit_Import(self, node):
		'''All work is done for plain imports in indexer.'''


	def visit_ImportFrom(self, node):
		'''Note: we need to already be indexed to provide names for * imports, so we _also_
			do import_from in link.'''


	def visit_ListComp(self, node):
		with self.push_scope(node.hl):
			self.visit_nodelist(node.generators)
			self.visit(node.elt)


	def visit_Name(self, node):
		if node.ctx in [py.Load, py.Del]:
			sym = self.scope.lookup(str(node))
			node.hl = NameRef(sym)


	def visit_SetComp(self, node):
		with self.push_scope(node.hl):
			self.visit_nodelist(node.generators)
			self.visit(node.elt)


	'''
	def visit_TryExcept(self, node):
		self.visit_nodelist(node.body)
		# do lookup on exception type's here
		for handler in node.handlers:
			if isinstance(handler.type, py.Tuple):
				for name in handler.type.elts:
					sym = self.scope.lookup(str(name))
					name.hl = NameRef(sym)
			elif isinstance(handler.type, (py.Name, py.Attribute, py.Subscript)):
				self.visit(handler.type)
			else:
				assert handler is node.handlers[-1], "default 'except' must be last"
			# NOTE: don't bother visiting the name, since we know it is a Store
			self.visit_nodelist(handler.body)
		self.visit_nodelist(node.orelse)
	'''

