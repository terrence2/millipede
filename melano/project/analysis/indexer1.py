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


class Indexer1(ASTVisitor):
	'''
	This finds all imports
	'''

	def __init__(self, project, module, visited):
		super().__init__()
		self.project = project
		self.module = module
		self.context = self.module

		# modules which have been visited
		self.visited = visited

		# anon scopes need to be unique
		self.anon_count = itertools.count()

		# count of symbols we weren't able to index because of missing dependencies
		self.missing = set()

	@contextmanager
	def new_scope(self, node, scope_ty=Scope, name=None):
		prior = self.context
		self.context = node.hl
		yield
		self.context = prior


	def visit_ClassDef(self, node):
		self.visit(node.name)
		self.visit_nodelist(node.bases)
		self.visit_nodelist(node.keywords)
		self.visit(node.starargs)
		self.visit(node.kwargs)
		with self.new_scope(node):
			self.visit_nodelist(node.body)
		self.visit_nodelist(node.decorator_list)


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

		with self.new_scope(node):
			# args
			self.visit_nodelist_field(node.args.args, 'arg')
			self.visit(node.args.vararg)
			self.visit_nodelist_field(node.args.kwonlyargs, 'arg')
			self.visit(node.args.kwarg)
			# body
			self.visit_nodelist(node.body)

		# decorators
		self.visit_nodelist(node.decorator_list)


	def visit_Import(self, node):
		for alias in node.names:
			if alias.asname:
				# Note: don't visit name if we have asname, since name is Load in this case, but it's not a Load on this module
				#self.visit(alias.asname)
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
					#self.visit(alias.name)
					alias.name.hl.scope = self.module.refs[str(alias.name)]


	def visit_ImportFrom(self, node):
		def _handle_star(alias):
			for name in mod.lookup_star():
				# don't visit until we have already collected all possible symbols in the parent
				if mod not in self.visited:
					logging.info("Skipping missing: {}".format(pkg_or_mod_name + '.*'))
					self.missing.add(pkg_or_mod_name + '.*')
					return
				# only add if we have not yet added it
				if not self.context.has_symbol(name):
					ref = NameRef(mod.lookup(name))
					ref.parent = self.context
					self.context.add_symbol(name, ref)

		# query the module (keeping in mind that this may be a package we want)
		pkg_or_mod_name = '.' * node.level + str(node.module)
		mod = self.module.refs.get(pkg_or_mod_name, None)
		node.module.hl = mod

		# NOTE: any inspection of main should be limited to runtime
		#  e.g. in pkg_resources, inspection of __requires__ with "from __main__ import __requires__"
		if pkg_or_mod_name == '__main__':
			return

		# if we have not visited the target module, skip it until we have
		if mod is None:
			logging.info("Skipping missing: {}".format(pkg_or_mod_name + '.*'))
			self.missing.add(pkg_or_mod_name + '.*')
			return

		for alias in node.names:
			if str(alias.name) == '*':
				_handle_star(alias)
				continue

			# Note: the queried name may be in the given module (maybe an __init__), or 
			#		it may be a submodule in the package of that name
			if mod.has_symbol(str(alias.name)):
				sym = mod.lookup(str(alias.name))

			elif mod.filename.endswith('__init__.py'):
				# ensure we have actually visited the real target before we go looking for submodules --
				# Note: if we _are_ '.' ourself, then we can continue here without issues
				if not self.module.filename.endswith('__init__.py') and mod not in self.visited:
					logging.info("Skipping missing from: {}".format(pkg_or_mod_name + '.' + str(alias.name)))
					self.missing.add(pkg_or_mod_name + '.' + str(alias.name))
					return

				# filename will be one of either (1) mod/name.py or (2) mod/name/__init__.py
				real_filename_1 = mod.filename[:-11] + str(alias.name).replace('.', '/') + '.py'
				real_filename_2 = mod.filename[:-11] + str(alias.name).replace('.', '/') + '/' + '__init__.py'
				try:
					sym = self.project.modules_by_path[real_filename_1]
				except KeyError:
					try:
						sym = self.project.modules_by_path[real_filename_2]
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


	def visit_Module(self, node):
		assert node.hl is self.module
		node.hl.owner.types = [PyModuleType]
		self.visit_nodelist(node.body)

