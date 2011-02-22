'''
Copyright (c) 2011, Terrence Cole.
All rights reserved.
'''
from contextlib import contextmanager
from melano.c.types.pydict import PyDictType
from melano.c.types.pyinteger import PyIntegerType
from melano.c.types.pymodule import PyModuleType
from melano.c.types.pystring import PyStringType
from melano.c.types.pytuple import PyTupleType
from melano.parser import ast
from melano.parser.visitor import ASTVisitor
from melano.project.constant import Constant
from melano.project.intermediate import Intermediate
from melano.project.name import Name
from melano.project.scope import Scope
import logging
import pdb
#from melano.project.class_ import MelanoClass
#from melano.project.foreign import ForeignObject
#from melano.project.function import MelanoFunction
#from melano.project.module import MelanoModule
#from melano.project.variable import MelanoVariable


class Indexer(ASTVisitor):
	'''
	Get the names of things in this module.
	'''

	def __init__(self, project, module):
		super().__init__()
		self.project = project
		self.module = module
		self.context = self.module


	@contextmanager
	def scope(self, node):
		# insert node into parent scope
		sym = self.context.add_symbol(str(node.name))
		sym.scope = Scope(sym)
		node.hl = sym.scope
		node.name.hl = sym

		# push a new scope
		prior = self.context
		self.context = sym.scope
		yield
		self.context = prior


	def visit_Module(self, node):
		assert node.hl is self.module
		node.hl.owner.types = [PyModuleType]
		self.visit_nodelist(node.body)


	def visit_Import(self, node):
		for alias in node.names:
			# If we have an asname then we are importing the full module foo.bar.baz and putting
			#	that module into the namespace under the asname.  If we don't, then we are only
			# really importing the first part of the module path -- foo of foo.bar.baz -- and we are
			# only putting that top name into the namespace.  If we have no asname, we need to
			# mangle the alias to provide the target asname and the real import name.
			self.visit(alias.name)
			self.visit(alias.asname)

			#TODO: this probably needs to be in the linker, where it can always succeed
			alias.name.hl.scope = self.module.refs.get(str(alias.name), None)


	def visit_ImportFrom(self, node):
		modname = '.' * node.level + str(node.module)
		mod = self.module.refs.get(modname, None)
		if not mod:
			return

		for alias in node.names:
			assert not isinstance(alias.name, ast.Attribute)
			name = str(alias.name)
			if name == '*':
				for n, ref in mod.lookup_star().items():
					self.context.add_symbol(n)
			else:
				self.visit(alias.name)
				self.visit(alias.asname)

				'''
				if alias.asname:
					asname = str(alias.asname)
				else:
					asname = name
				try:
					self.context.add_symbol(asname)
					#ref = mod.lookup_name(name)
					#self.context.names[asname] = ref
				except KeyError:
					logging.critical("MISSING: {} in {} @ {}".format(name, mod.filename, self.module.filename))
				'''


	def visit_ClassDef(self, node):
		self.visit_nodelist(node.bases)
		self.visit_nodelist(node.keywords)
		self.visit(node.starargs)
		self.visit(node.kwargs)
		with self.scope(node):
			self.visit_nodelist(node.body)
		self.visit_nodelist(node.decorator_list)


	def visit_FunctionDef(self, node):
		self.visit(node.name)
		self.visit(node.returns) # return annotation
		self.visit_nodelist_field(node.args.args, 'annotation') # position arg annotations
		self.visit(node.args.varargannotation) # *args annotation
		self.visit_nodelist_field(node.args.kwonlyargs, 'annotation') # kwargs annotation
		self.visit(node.args.kwargannotation) # **args annotation
		self.visit_nodelist(node.args.defaults) # positional arg default values
		self.visit_nodelist(node.args.kw_defaults) # kwargs default values

		with self.scope(node):
			# arg name defs are inside the func
			self.visit_nodelist_field(node.args.args, 'arg')
			self.visit(node.args.vararg)
			self.visit_nodelist_field(node.args.kwonlyargs, 'arg')
			self.visit(node.args.kwarg)

			self.visit_nodelist(node.body)

		# insert the assumed return None if we fall off the end without a return
		if not isinstance(node.body[-1], ast.Return):
			node.body.append(ast.Return(None, None))

		self.visit_nodelist(node.decorator_list)


	def visit_Attribute(self, node):
		self.visit(node.value)
		self.visit(node.attr)
		name = str(node)
		if name not in self.context.symbols:
			sym = self.context.add_symbol(name)
			node.hl = sym
		else:
			node.hl = self.context.lookup(name)


	def visit_Dict(self, node):
		node.hl = Constant(PyDictType)
		if node.keys and node.values:
			for k, v in zip(node.keys, node.values):
				self.visit(k)
				self.visit(v)


	def visit_Global(self, node):
		for name in node.names:
			if name not in self.context.symbols:
				self.context.add_symbol(name)
			self.context.lookup(name).is_global = True


	def visit_Nonlocal(self, node):
		for name in node.names:
			if name not in self.context.symbols:
				self.context.add_symbol(name)
			self.context.lookup(name).is_nonlocal = True


	def visit_Name(self, node):
		name = str(node)
		if name not in self.context.symbols:
			sym = self.context.add_symbol(name)
			node.hl = sym
		else:
			node.hl = self.context.lookup(name)
		if node.ctx == ast.Store and not node.hl.is_nonlocal and not node.hl.is_global:
			self.context.mark_ownership(name)


	def visit_Num(self, node):
		#TODO: expand this to discover the minimum sized int that will cover the value.
		#TODO: does Num also cover PyFloatTypes?
		node.hl = Constant(PyIntegerType)


	def visit_Str(self, node):
		#TODO: discover if we can use a non-unicode or c string type?
		node.s = node.s.strip('"').strip("'")
		node.hl = Constant(PyStringType)


	def visit_Tuple(self, node):
		node.hl = Constant(PyTupleType)
		self.visit_nodelist(node.elts)
