'''
Copyright (c) 2011, Terrence Cole.
All rights reserved.
'''
from contextlib import contextmanager
from melano.hl.class_ import MelanoClass
from melano.hl.comprehension import MelanoComprehension
from melano.hl.constant import Constant
from melano.hl.function import MelanoFunction
from melano.hl.name import Name
from melano.hl.nameref import NameRef
from melano.hl.scope import Scope
from melano.hl.types.pybytes import PyBytesType
from melano.hl.types.pydict import PyDictType
from melano.hl.types.pyfloat import PyFloatType
from melano.hl.types.pyinteger import PyIntegerType
from melano.hl.types.pylist import PyListType
from melano.hl.types.pymodule import PyModuleType
from melano.hl.types.pyset import PySetType
from melano.hl.types.pystring import PyStringType, MalformedStringError
from melano.hl.types.pytuple import PyTupleType
from melano.lang.visitor import ASTVisitor
from melano.py import ast as py
import itertools
import logging
import pdb


class Indexer0(ASTVisitor):
	'''
	This builds the high-level scope tree.
	'''
	def __init__(self, project, module):
		super().__init__()
		self.project = project
		self.module = module
		self.context = self.module

		# anon scopes need to be unique
		self.anon_count = itertools.count()

		# count of symbols we weren't able to index because of missing dependencies
		self.missing = set()


	@contextmanager
	def new_scope(self, node, scope_ty=Scope, name=None):
		# NOTE: since we can repeatedly visit index to find names defined later, we need
		#		to not overwrite existing symbols dicts
		if node.hl:
			prior = self.context
			self.context = node.hl
			yield
			self.context = prior
			return

		if name is None:
			name = str(node.name)

		# insert node into parent scope
		sym = self.context.add_symbol(name)
		sym.scope = scope_ty(sym)
		node.hl = sym.scope
		try: node.name.hl = sym
		except: pass

		# push a new scope
		prior = self.context
		self.context = sym.scope
		yield
		self.context = prior


	def find_nearest_function(self, base):
		cur = base
		while cur:
			if isinstance(cur, MelanoFunction):
				return cur
			cur = cur.owner.parent
		return None


	def visit_Bytes(self, node):
		node.hl = Constant(PyBytesType())


	def visit_ClassDef(self, node):
		self.visit(node.name)
		self.visit_nodelist(node.bases)
		self.visit_nodelist(node.keywords)
		self.visit(node.starargs)
		self.visit(node.kwargs)
		with self.new_scope(node, scope_ty=MelanoClass):
			self.visit_nodelist(node.body)
		self.visit_nodelist(node.decorator_list)


	def visit_Dict(self, node):
		node.hl = Constant(PyDictType())
		if node.keys and node.values:
			for k, v in zip(node.keys, node.values):
				self.visit(k)
				self.visit(v)


	def visit_DictComp(self, node):
		name = 'dictcomp_scope_' + str(next(self.anon_count))
		with self.new_scope(node, scope_ty=MelanoComprehension, name=name):
			self.visit(node.key)
			self.visit(node.value)
			self.visit_nodelist(node.generators)


	def visit_FunctionDef(self, node):
		# name
		self.visit(node.name)
		# annotations
		self.visit(node.returns)
		self.visit_nodelist_field(node.args.args, 'annotation') # position arg annotations
		self.visit(node.args.varargannotation) # *args annotation
		self.visit_nodelist_field(node.args.kwonlyargs, 'annotation') # kwargs annotation
		self.visit(node.args.kwargannotation) # **args annotation
		# defaults
		self.visit_nodelist(node.args.defaults) # positional arg default values
		self.visit_nodelist(node.args.kw_defaults) # kwargs default values

		with self.new_scope(node, scope_ty=MelanoFunction):
			if self.find_nearest_function(self.context.owner.parent):
				self.context.set_needs_closure()

			# args
			self.visit_nodelist_field(node.args.args, 'arg')
			self.visit(node.args.vararg)
			self.visit_nodelist_field(node.args.kwonlyargs, 'arg')
			self.visit(node.args.kwarg)
			# body
			self.visit_nodelist(node.body)

		# decorators
		self.visit_nodelist(node.decorator_list)


	def visit_GeneratorExp(self, node):
		name = 'genexp_scope_' + str(next(self.anon_count))
		node.name = py.Name(name, py.Store, None)
		self.visit(node.name)
		with self.new_scope(node, scope_ty=MelanoFunction, name=name):
			self.context.is_generator = True
			self.context.is_anonymous = True
			self.context.set_needs_closure()
			self.visit(node.elt)
			self.visit_nodelist(node.generators)


	def visit_Global(self, node):
		for name in node.names:
			#NOTE: this scope may be the only creator of this symbol (e.g. no Name Store), so we 
			#		need to make sure that the symbol gets created on the module scope too
			if name not in self.module.symbols:
				self.module.add_symbol(name)
			sym = self.module.lookup(name)
			ref = self.context.set_reference(sym)
			ref.is_global = True


	'''
	def visit_Import(self, node):
		for alias in node.names:
			if alias.asname:
				# Note: don't visit name if we have asname, since name is Load in this case, but it's not a Load on this module
				self.visit(alias.asname)
				alias.asname.hl.scope = self.module.refs[str(alias.name)]
			else:
				if isinstance(alias.name, py.Attribute):
					assert alias.name.is_all_names()
					parts = []
					for name in alias.name.get_names():
						# NOTE: don't bother visiting, since this recorded as a Load
						name.set_context(py.Store)
						name.hl = Name(str(name), self.context)
						if name is alias.name.first():
							self.context.symbols[str(name)] = name.hl
						# find the real name of this part of the module and create a ref to the underlying module
						parts.append(str(name))
						fullname = '.'.join(parts)
						name.hl.scope = self.module.refs[fullname]
				else:
					self.visit(alias.name)
					alias.name.hl.scope = self.module.refs[str(alias.name)]


	def visit_ImportFrom(self, node):
		# query the module (keeping in mind that this may be a package we want)
		pkg_or_mod_name = '.' * node.level + str(node.module)
		mod = self.module.refs.get(pkg_or_mod_name, None)
		node.module.hl = mod

		if mod is None:
			logging.info("Skipping missing: {}".format(pkg_or_mod_name + '.*'))
			self.missing.add(pkg_or_mod_name + '.*')
			return

		for alias in node.names:
			if str(alias.name) == '*':
				for name in mod.lookup_star():
					# don't visit until we have already visited the parent
					if mod not in self.visited:
						logging.info("Skipping missing: {}".format(pkg_or_mod_name + '.*'))
						self.missing.add(pkg_or_mod_name + '.*')
						return
					if not self.context.has_symbol(name):
						ref = NameRef(mod.lookup(name))
						ref.parent = self.context
						self.context.add_symbol(name, ref)
				continue

			# Note: the queried name may be in the given module (maybe an __init__), or 
			#		it may be a submodule in the package of that name
			if mod.has_symbol(str(alias.name)):
				sym = mod.lookup(str(alias.name))
			elif mod.filename.endswith('__init__.py'):
				# ensure we have actually visited the real target before we go looking for submodules --
				# Note: if we _are_ '.' outself, then we can continue here without issues
				if not self.module.filename.endswith('__init__.py') and mod not in self.visited:
					logging.info("Skipping missing from: {}".format(pkg_or_mod_name + '.' + str(alias.name)))
					self.missing.add(pkg_or_mod_name + '.' + str(alias.name))
					return
				real_filename = mod.filename[:-11] + str(alias.name).replace('.', '/') + '.py'
				try:
					sym = self.project.modules_by_path[real_filename]
				except KeyError:
					logging.info("Skipping missing from: {}".format(pkg_or_mod_name + '.' + str(alias.name)))
					self.missing.add(pkg_or_mod_name + '.' + str(alias.name))
					return
			else:
				logging.info("Skipping missing from: {}".format(pkg_or_mod_name + '.' + str(alias.name)))
				self.missing.add(pkg_or_mod_name + '.' + str(alias.name))
				continue

			ref = NameRef(sym)
			ref.parent = self.context

			if alias.asname:
				#self.visit(alias.asname)
				self.context.add_symbol(str(alias.asname), ref)
				alias.asname.hl = ref
				alias.name.hl = ref
			else:
				#self.visit(alias.name)
				self.context.add_symbol(str(alias.name), ref)
				alias.name.hl = ref
	'''

	def visit_Lambda(self, node):
		#defaults
		self.visit_nodelist(node.args.defaults) # positional arg default values
		self.visit_nodelist(node.args.kw_defaults) # kwargs default values
		#name
		name = 'lambda_scope_' + str(next(self.anon_count))
		node.name = py.Name(name, py.Store, None)
		self.visit(node.name)
		with self.new_scope(node, scope_ty=MelanoFunction):
			if self.find_nearest_function(self.context.owner.parent):
				self.context.set_needs_closure()
			self.context.is_anonymous = True
			# args
			self.visit_nodelist_field(node.args.args, 'arg')
			self.visit(node.args.vararg)
			self.visit_nodelist_field(node.args.kwonlyargs, 'arg')
			self.visit(node.args.kwarg)
			#body
			self.visit_nodelist(node.body)


	def visit_List(self, node):
		node.hl = Constant(PyListType())
		self.visit_nodelist(node.elts)


	def visit_ListComp(self, node):
		name = 'listcomp_scope_' + str(next(self.anon_count))
		with self.new_scope(node, scope_ty=MelanoComprehension, name=name):
			self.visit(node.elt)
			self.visit_nodelist(node.generators)


	def visit_Module(self, node):
		assert node.hl is self.module
		node.hl.owner.types = [PyModuleType]
		self.visit_nodelist(node.body)


	def visit_Name(self, node):
		if node.ctx in [py.Store, py.Param, py.Aug]:
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
		assert self.context.has_closure

		for name in node.names:
			try:
				# look up-scope for the name
				sym = self.context.get_next_scope().lookup(name)
			except KeyError:
				self.missing.add(name)
				return
			ref = self.context.set_reference(sym)
			ref.is_nonlocal = True


	def visit_Num(self, node):
		#TODO: expand this to discover the minimum sized int that will cover the value.
		if isinstance(node.n, int):
			node.hl = Constant(PyIntegerType())
		else:
			node.hl = Constant(PyFloatType())


	def visit_Set(self, node):
		node.hl = Constant(PySetType())
		self.visit_nodelist(node.elts)


	def visit_SetComp(self, node):
		name = 'setcomp_scope_' + str(next(self.anon_count))
		with self.new_scope(node, scope_ty=MelanoComprehension, name=name):
			self.visit(node.elt)
			self.visit_nodelist(node.generators)


	def visit_Str(self, node):
		#TODO: discover if we can use a non-unicode or c string type?
		node.hl = Constant(PyStringType())


	def visit_TryExcept(self, node):
		self.visit_nodelist(node.body)
		for handler in node.handlers:
			if handler.name:
				name = str(handler.name)
				if name not in self.context.symbols:
					sym = self.context.add_symbol(name)
					handler.name.hl = sym
				# if we store to the same name multiple times in a scope, assign the ref or sym to the ll ast at each point it is used
				if not handler.name.hl:
					handler.name.hl = self.context.lookup(name)
			#NOTE: don't bother visiting the exception type, because we know it is a Load
			self.visit_nodelist(handler.body)
		self.visit_nodelist(node.orelse)


	def visit_Tuple(self, node):
		node.hl = Constant(PyTupleType())
		self.visit_nodelist(node.elts)


	def visit_Yield(self, node):
		assert isinstance(self.context, MelanoFunction), 'Yield in non-function scope'
		self.context.is_generator = True
		self.visit(node.value)
