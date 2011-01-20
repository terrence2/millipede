'''
Copyright (c) 2011, Terrence Cole.
All rights reserved.
'''
from contextlib import contextmanager
from melano.parser import ast
from melano.parser.visitor import ASTVisitor
from melano.project.class_ import MelanoClass
from melano.project.function import MelanoFunction
from melano.project.variable import MelanoVariable
import logging


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
	def scope(self, metype):
		# insert node into parent scope
		self.context.names[str(metype)] = metype

		# push a new scope
		prior = metype.parent = self.context
		self.context = metype
		yield
		self.context = prior


	def visit_Import(self, node):
		for alias in node.names:
			if alias.asname:
				# e.g.: import foo(.bar.baz)? as bar
				name = str(alias.name)
				asname = str(alias.asname)
				self.context.names[asname] = self.module.refs[name]
			else:
				if isinstance(alias.name, ast.Attribute):
					# e.g.: import foo.bar.baz
					name = str(alias.name)
					asname = str(alias.name.first())
					self.context.names[asname] = self.project.find_module(asname, self)
				else:
					# e.g.: import foo
					name = str(alias.name)
					self.context.names[name] = self.module.refs[name]


	def visit_ImportFrom(self, node):
		#NOTE: modules are be loaded in _mostly_ dependency order so that we can perform module level
		#		lookups here.  These will also include non-module lookups, but these we can skip for now.
		# 		We can't do full dependency ordering because of weird star/graph relationships.  We will need
		#		to re-run lookup by the total depth of from foo import bar chains.  In practice this is 2, so
		#		just re-doing missed entries in the linker is adequate. 

		# find the module
		modname = '.' * node.level + str(node.module)
		mod = self.module.refs[modname]
		if mod is None: return

		for alias in node.names:
			assert not isinstance(alias.name, ast.Attribute)
			name = str(alias.name)
			if name == '*':
				for n, ref in mod.lookup_star().items():
					self.context.names[n] = ref
			else:
				if alias.asname:
					asname = str(alias.asname)
				else:
					asname = name
				try:
					ref = mod.lookup_name(name)
					self.context.names[asname] = ref
				except KeyError:
					logging.critical("MISSING: {} in {} @ {}".format(name, mod.filename, self.module.filename))


	def visit_ClassDef(self, node):
		self.visit_nodelist(node.bases)
		self.visit_nodelist(node.keywords)
		self.visit(node.starargs)
		self.visit(node.kwargs)
		with self.scope(MelanoClass(node)):
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

		with self.scope(MelanoFunction(node)):
			# arg name defs are inside the func
			self.visit_nodelist_field(node.args.args, 'arg')
			self.visit(node.args.vararg)
			self.visit_nodelist_field(node.args.kwonlyargs, 'arg')
			self.visit(node.args.kwarg)

			self.visit_nodelist(node.body)

		self.visit_nodelist(node.decorator_list)


	def visit_Name(self, node):
		name = str(node)
		if node.ctx == ast.Param or node.ctx == ast.Store:
			if name not in self.context.names:
				self.context.names[name] = MelanoVariable(node, self.context)

