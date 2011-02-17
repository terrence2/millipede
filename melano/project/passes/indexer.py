'''
Copyright (c) 2011, Terrence Cole.
All rights reserved.
'''
from contextlib import contextmanager
from melano.c.types.pyinteger import PyIntegerType
from melano.c.types.pymodule import PyModuleType
from melano.parser import ast
from melano.parser.visitor import ASTVisitor
from melano.project.constant import Constant
from melano.project.name import Name
from melano.project.scope import Scope
import logging
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
		node.hl = node.name.hl = sym

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
			if alias.asname:
				# e.g.: import foo(.bar.baz)? as bar
				name = str(alias.name)
				asname = str(alias.asname)
				if self.project.is_local(self.module):
					self.context.add_symbol(asname)
					#self.context.names[asname] = self.module.refs[name]
				else:
					self.context.add_symbol(asname)
					#self.context.names[asname] = ForeignObject(name)
				#alias.asname.hl = self.context.names[asname]
			else:
				if isinstance(alias.name, ast.Attribute):
					# e.g.: import foo.bar.baz
					name = str(alias.name)
					asname = str(alias.name.first())
					if self.project.is_local(self.module):
						self.context.add_symbol(asname)
						#alias.name.hl = self.context.names[asname] = self.project.find_module(asname, self)
					else:
						self.context.add_symbol(name)
						#alias.name.hl = self.context.names[name] = ForeignObject(asname)
				else:
					# e.g.: import foo
					name = str(alias.name)
					if self.project.is_local(self.module):
						self.context.add_symbol(name)
						#self.context.names[name] = self.module.refs[name]
					else:
						self.context.add_symbol(name)
						#self.context.names[name] = ForeignObject(name)
					#alias.name.hl = self.context.names[name]


	def visit_ImportFrom(self, node):
		if not self.project.is_local(self.module):
			return
		#NOTE: modules are be loaded in _mostly_ dependency order so that we can perform module level
		#		lookups here.  These will also include non-module lookups, but these we can skip for now.
		# 		We can't do full dependency ordering because of weird star/graph relationships.  We will need
		#		to re-run lookup by the total depth of from foo import bar chains.  In practice this is 2, so
		#		just re-doing missed entries in the linker is adequate. 

		# find the module
		modname = '.' * node.level + str(node.module)
		try:
			mod = self.module.refs[modname]
		except:
			import pdb;pdb.set_trace()
		if mod is None: return

		for alias in node.names:
			assert not isinstance(alias.name, ast.Attribute)
			name = str(alias.name)
			if name == '*':
				for n, ref in mod.lookup_star().items():
					#self.context.names[n] = ref
					self.context.add_symbol(n)
			else:
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


	def visit_ClassDef(self, node):
		self.visit_nodelist(node.bases)
		self.visit_nodelist(node.keywords)
		self.visit(node.starargs)
		self.visit(node.kwargs)
		with self.scope(node):
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
		#name = str(node).replace('.', '_')
		name = str(node)
		#if node.ctx == ast.Store:
		if name not in self.context.symbols:
			sym = self.context.add_symbol(name)
			node.hl = sym
		else:
			node.hl = self.context.lookup(name)



	def visit_Name(self, node):
		name = str(node)
		#if node.ctx == ast.Param or node.ctx == ast.Store:
		if name not in self.context.symbols:
			sym = self.context.add_symbol(name)
			node.hl = sym
		else:
			node.hl = self.context.lookup(name)


	def visit_Num(self, node):
		#TODO: expand this to discover the minimum sized int that will cover the value.
		#TODO: does Num also cover PyFloatTypes?
		node.hl = Constant(PyIntegerType)
