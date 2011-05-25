'''
Copyright (c) 2011, Terrence Cole.
All rights reserved.
'''
from contextlib import contextmanager
from melano.hl.nodes.call import Call
from melano.hl.nodes.coerce import Coerce
from melano.hl.nodes.entity import Entity
from melano.hl.nodes.name import Name
from melano.hl.nodes.nameref import NameRef
from melano.hl.nodes.subscript import Subscript
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
		self.scope = self.module


	@contextmanager
	def push_scope(self, ctx):
		# push a new scope
		prior = self.scope
		self.scope = ctx
		yield
		self.scope = prior


	def visit_Attribute(self, node):
		# Note: references through the lhs of an attribute are always a ref, not a name, so we need to do
		#		attribute value updates in linking
		self.visit(node.value)

		# note that the attribute almost certainly has no hl value here now -- we will eventually propagate
		#		correct type info into the attribute at, e.g. assignment, because we assign this attribute node
		#		as a ref into the name we create here on the actual attribute.
		assert node.attr.hl is None
		node.attr.hl = Name(str(node.attr), node.value.hl, node)
		node.hl = NameRef(node.attr.hl)
		node.value.hl.add_attribute(str(node.attr), node.attr.hl, node)


	def visit_AugAssign(self, node):
		self.visit(node.value)
		self.visit(node.target)
		node.target.hl.add_type(node.value.hl.get_type())
		node.hl = Coerce(Coerce.INPLACE, node, node.target.hl, node.value.hl)


	def visit_BinOp(self, node):
		self.visit(node.left)
		self.visit(node.right)
		node.hl = Coerce(Coerce.GENERALIZE, node, node.left.hl, node.right.hl)


	def visit_BoolOp(self, node):
		self.visit_nodelist(node.values)
		node.hl = Coerce(Coerce.BOOLEAN, node, [v.hl for v in node.values])


	def visit_Call(self, node):
		self.visit(node.func)
		self.visit_nodelist(node.args)
		self.visit_nodelist(node.keywords)
		self.visit(node.starargs)
		self.visit(node.kwargs)
		node.hl = Call(node.func.hl, node)


	def visit_ClassDef(self, node):
		self.visit(node.name)
		self.visit_nodelist(node.bases)
		self.visit_nodelist(node.keywords)
		self.visit(node.starargs)
		self.visit(node.kwargs)
		with self.push_scope(node.hl):
			self.visit_nodelist(node.body)
		self.visit_nodelist(node.decorator_list)


	def visit_Delete(self, node):
		for target in node.targets:
			self.visit(target)


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


	def visit_IfExp(self, node):
		self.visit(node.test)
		self.visit(node.body)
		self.visit(node.orelse)
		node.hl = Entity(node)


	def visit_Import(self, node):
		'''All work is done for plain imports in indexer.'''


	def visit_ImportFrom(self, node):
		'''Note: we need to already be indexed to provide names for * imports, so we _also_
			do import_from in link.'''


	def visit_Index(self, node):
		self.visit(node.value)
		node.hl = node.value.hl


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


	def visit_Slice(self, node):
		self.visit(node.lower)
		self.visit(node.upper)
		self.visit(node.step)


	def visit_Subscript(self, node):
		# Note: references through the lhs of a subscript are always a ref, not a name, so we need to do
		#		attribute value updates in linking
		self.visit(node.value)
		self.visit(node.slice)
		node.hl = Subscript(node.value.hl, node.slice, node)


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


	def visit_Tuple(self, node):
		self.visit_nodelist(node.elts)
		#for i, e in enumerate(node.elts):
		#	node.hl.add_subscript(i, e.get_type())


	def visit_UnaryOp(self, node):
		self.visit(node.operand)
		if node.op == py.Not:
			node.hl = Coerce(Coerce.BOOLEAN, node, node.operand.hl)
		else:
			node.hl = Coerce(Coerce.INPLACE, node, node.operand.hl)

