'''
Copyright (c) 2011, Terrence Cole.
All rights reserved.
'''
from contextlib import contextmanager
from melano.parser import ast
from melano.parser.visitor import ASTVisitor


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


	def visit_ImportFrom(self, node):
		# find the module
		modname = '.' * node.level + str(node.module)
		mod = self.module.refs[modname]
		if mod is None: return

		print("import from: {}".format(mod.filename))
		for alias in node.names:
			assert not isinstance(alias.name, ast.Attribute)
			name = str(alias.name)
			if name == '*':
				for n, ref in mod.lookup_star().items():
					if n not in self.context.names:
						self.context.names[n] = ref
			else:
				if alias.asname:
					asname = str(alias.asname)
				else:
					asname = name
				if asname not in self.context.names:
					try:
						ref = mod.lookup_name(name)
						self.context.names[asname] = ref
					except KeyError:
						try:
							# the name could also be a sub-module under the module
							ref = self.project.find_module(modname + '.' + name, self)
							self.context.names[asname] = ref
						except KeyError:
							if not mod.filename.endswith('.py'):
								print("SKIPPING NAME: {} in {}".format(name, mod.filename))
							else:
								import pdb; pdb.set_trace()


	def visit_ClassDef(self, node):
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


