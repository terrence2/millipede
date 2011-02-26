'''
Copyright (c) 2011, Terrence Cole.
All rights reserved.
'''
from contextlib import contextmanager
from melano.c.types.pybytes import PyBytesType
from melano.c.types.pydict import PyDictType
from melano.c.types.pyfloat import PyFloatType
from melano.c.types.pyinteger import PyIntegerType
from melano.c.types.pylist import PyListType
from melano.c.types.pymodule import PyModuleType
from melano.c.types.pyset import PySetType
from melano.c.types.pystring import PyStringType
from melano.c.types.pytuple import PyTupleType
from melano.parser import ast as py
from melano.parser.visitor import ASTVisitor
from melano.project.constant import Constant
from melano.project.function import MelanoFunction
from melano.project.intermediate import Intermediate
from melano.project.name import Name
from melano.project.scope import Scope
import logging
import pdb


class Indexer(ASTVisitor):
	'''
	This builds the high-level scope tree.
	'''

	def __init__(self, project, module):
		super().__init__()
		self.project = project
		self.module = module
		self.context = self.module


	@contextmanager
	def scope(self, node, scope_ty=Scope):
		# insert node into parent scope
		sym = self.context.add_symbol(str(node.name))
		sym.scope = scope_ty(sym)
		node.hl = sym.scope
		node.name.hl = sym

		# push a new scope
		prior = self.context
		self.context = sym.scope
		yield
		self.context = prior


	def visit_Bytes(self, node):
		node.s = node.s.strip('"').strip("'")
		node.hl = Constant(PyBytesType)


	def visit_ClassDef(self, node):
		self.visit(node.name)
		self.visit_nodelist(node.bases)
		self.visit_nodelist(node.keywords)
		self.visit(node.starargs)
		self.visit(node.kwargs)
		with self.scope(node):
			self.visit_nodelist(node.body)
		self.visit_nodelist(node.decorator_list)


	def visit_Dict(self, node):
		node.hl = Constant(PyDictType)
		if node.keys and node.values:
			for k, v in zip(node.keys, node.values):
				self.visit(k)
				self.visit(v)


	def visit_DictComp(self, node):
		with self.scope(node):
			self.visit(node.key)
			self.visit(node.value)
			self.visit_nodelist(node.generators)


	def visit_FunctionDef(self, node):
		self.visit(node.name)
		self.visit(node.returns) # return annotation
		self.visit_nodelist_field(node.args.args, 'annotation') # position arg annotations
		self.visit(node.args.varargannotation) # *args annotation
		self.visit_nodelist_field(node.args.kwonlyargs, 'annotation') # kwargs annotation
		self.visit(node.args.kwargannotation) # **args annotation
		self.visit_nodelist(node.args.defaults) # positional arg default values
		self.visit_nodelist(node.args.kw_defaults) # kwargs default values

		with self.scope(node, scope_ty=MelanoFunction):
			# arg name defs are inside the func
			self.visit_nodelist_field(node.args.args, 'arg')
			self.visit(node.args.vararg)
			self.visit_nodelist_field(node.args.kwonlyargs, 'arg')
			self.visit(node.args.kwarg)

			# add call conventions to the scope
			if node.args and node.args.args:
				for arg in node.args.args:
					self.context.expect_args.append(str(arg.arg))
			if node.args and node.args.kwonlyargs:
				for arg in node.args.kwonlyargs:
					self.context.expect_kwargs.add(str(arg.arg))

			self.visit_nodelist(node.body)

		# insert the assumed return None if we fall off the end without a return
		if not isinstance(node.body[-1], py.Return):
			node.body.append(py.Return(None, None))

		self.visit_nodelist(node.decorator_list)


	def visit_GeneratorExp(self, node):
		with self.scope(node):
			self.visit(node.elt)
			self.visit_nodelist(node.generators)


	def visit_Global(self, node):
		for name in node.names:
			#NOTE: this scope may be the only creator of this symbol (e.g. no Name Store), so we 
			#		need to make sure that the symbol gets created on the module scope too
			if name not in self.module.symbols:
				self.module.add_symbol(name)
			sym = self.module.lookup(name)
			ref = self.context.add_reference(sym)
			ref.is_global = True


	def visit_Import(self, node):
		for alias in node.names:
			if alias.asname:
				# Note: don't visit name if we have asname, since name is Load in this case, but it's not a Load on this module
				self.visit(alias.asname)
				alias.asname.hl.scope = self.module.refs.get(str(alias.name), None)
			else:
				self.visit(alias.name)
				alias.name.hl.scope = self.module.refs.get(str(alias.name), None)


	def visit_ImportFrom(self, node):
		#Note: we need to already be indexed to provide name refs that are _inside_ a module,
		#	so we do most of the work for ImportFrom in link.
		for alias in node.names:
			if alias.asname:
				self.visit(alias.asname)
			else:
				if str(alias.name) != '*':
					self.visit(alias.name)


	def visit_Lambda(self, node):
		with self.scope(node):
			self.visit_nodelist_field(node.args.args, 'arg')
			self.visit(node.args.vararg)
			self.visit_nodelist_field(node.args.kwonlyargs, 'arg')
			self.visit(node.args.kwarg)
			self.visit(node.body)


	def visit_List(self, node):
		node.hl = Constant(PyListType)
		self.visit_nodelist(node.elts)


	def visit_ListComp(self, node):
		with self.scope(node):
			self.visit(node.elt)
			self.visit_nodelist(node.generators)


	def visit_Module(self, node):
		assert node.hl is self.module
		node.hl.owner.types = [PyModuleType]
		self.visit_nodelist(node.body)


	def visit_Name(self, node):
		if node.ctx in [py.Store, py.Param]:
			#NOTE: store to global/nonlocal will have already visited the global/nonlocal node and created
			#		this name as a ref, thus preventing us from doing the (incorrect) lookup here
			name = str(node)
			if name not in self.context.symbols:
				sym = self.context.add_symbol(name)
				node.hl = sym
			# if we store to the same name multiple times in a scope, assign the ref or sym to the ll ast at each point it is used
			if not node.hl:
				node.hl = self.context.lookup(name)


	def visit_Nonlocal(self, node):
		for name in node.names:
			# look up-scope for the name
			#FIXME: we need to fully visit outer scopes first -- this may have to wait until link time? (function_nonlocal_late)
			sym = self.context.owner.parent.lookup(name)
			ref = self.context.add_reference(sym)
			ref.is_nonlocal = True


	def visit_Num(self, node):
		#TODO: expand this to discover the minimum sized int that will cover the value.
		if isinstance(node.n, int):
			node.hl = Constant(PyIntegerType)
		else:
			node.hl = Constant(PyFloatType)


	def visit_Set(self, node):
		node.hl = Constant(PySetType)
		self.visit_nodelist(node.elts)


	def visit_SetComp(self, node):
		with self.scope(node):
			self.visit(node.elt)
			self.visit_nodelist(node.generator)


	def visit_Str(self, node):
		#TODO: discover if we can use a non-unicode or c string type?
		node.s = node.s.strip('"').strip("'")
		node.hl = Constant(PyStringType)


	def visit_Tuple(self, node):
		node.hl = Constant(PyTupleType)
		self.visit_nodelist(node.elts)


	def visit_Yield(self, node):
		assert isinstance(self.context, MelanoFunction), 'Yield in non-function scope'
		self.scope.is_generator = True
