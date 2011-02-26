'''
Copyright (c) 2011, Terrence Cole.
All rights reserved.
'''
from contextlib import contextmanager
from melano.py import ast as py
from melano.lang.visitor import ASTVisitor
from melano.project.module import MelanoModule
from melano.project.nameref import NameRef
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


	#def visit_Attribute(self, node):
	#	# look up the attribute type and propagate it to a reference on the top-level attribute node
	#	if node.ctx == py.Load:
	#		self.visit(node.value)
	#		ref = node.value.hl.reference_attribute(str(node.attr))
	#		node.hl = ref


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


	'''
	def visit_Module(self, node):
		node.hl = self.module
		self.visit_nodelist(node.body)


	def visit_ImportFrom(self, node):
		# find the module
		modname = '.' * node.level + str(node.module)
		mod = self.module.refs[modname]
		if mod is None: return

		#print("import from: {}".format(mod.filename))
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
				if self.project.is_local(mod):
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
				else:
					self.context.names[asname] = ForeignObject(asname)


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


	def visit_Name(self, node):
		if node.ctx == ast.Load:
			ref = self.context.lookup(str(node))
			node.hl = ref
			#print("VISIT: {} -> {} -> {}".format(str(node), type(ref), node.hl))


	def visit_Attribute(self, node):
		if node.ctx == ast.Load:
			self.visit(node.value)
			lhs = node.value.hl
			if isinstance(lhs, MelanoModule):
				if self.project.is_local(lhs):
					node.hl = lhs.lookup(node.attr)
				else:
					node.hl = ForeignObject(node.attr)
			else:
				# NOTE: we only care about cross-module linkage at this point
				pass
	'''
