'''
Copyright (c) 2011, Terrence Cole.
All rights reserved.
'''
from contextlib import contextmanager
from melano.hl.module import MelanoModule
from melano.hl.name import Name
from melano.hl.nameref import NameRef
from melano.lang.visitor import ASTVisitor
from melano.py import ast as py
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


	def visit_Attribute(self, node):
		# Note: references through the lhs of an attribute are always a ref, not a name, so we need to do
		#		attribute value updates in linking
		self.visit(node.value)

		# note that the attribute almost certainly has no hl value here now -- we will eventually propagate
		#		correct type info into the attribute at, e.g. assignment, because we assign this attribute node
		#		as a ref into the name we create here on the actual attribute.
		assert node.attr.hl is None
		node.attr.hl = Name(str(node.attr), node.value.hl)
		node.hl = NameRef(node.attr.hl)
		node.value.hl.add_attribute(str(node.attr), node.attr.hl)


	def visit_Subscript(self, node):
		# Note: references through the lhs of an attribute are always a ref, not a name, so we need to do
		#		attribute value updates in linking
		self.visit(node.value)
		self.visit(node.slice)

		# note that the indexed  almost certainly has no hl value here now -- we will eventually propagate
		#		correct type info into the index at, e.g. assignment, because we assign this index node
		#		as a ref into the name we create here on the actual index
		assert node.slice.hl is None
		node.slice.hl = Name(str(node.slice), node.value.hl)
		node.hl = NameRef(node.slice.hl)
		node.value.hl.add_subscript(node.slice, node.slice.hl)


	def visit_DictComp(self, node):
		with self.scope(node.hl):
			self.visit_nodelist(node.generators)
			self.visit(node.key)
			self.visit(node.value)


	def visit_Call(self, node):
		self.visit(node.func)
		self.visit_nodelist(node.args)
		self.visit_nodelist(node.keywords)
		self.visit_nodelist(node.starargs)
		self.visit_nodelist(node.kwargs)
		node.hl = node.func.hl


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
		node.module.hl = mod

		for alias in node.names:
			assert not isinstance(alias.name, py.Attribute)
			if alias.asname:
				self.visit(alias.asname)
			else:
				if str(alias.name) == '*':
					for name in mod.lookup_star():
						self.context.add_symbol(name)
				else:
					self.visit(alias.name)


	def visit_ListComp(self, node):
		with self.scope(node.hl):
			self.visit_nodelist(node.generators)
			self.visit(node.elt)


	def visit_Name(self, node):
		if node.ctx == py.Load:
			sym = self.context.lookup(str(node))
			ref = self.context.add_reference(sym)
			node.hl = ref


	def visit_SetComp(self, node):
		with self.scope(node.hl):
			self.visit_nodelist(node.generators)
			self.visit(node.elt)


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
		self.visit_nodelist(node.orelse)
