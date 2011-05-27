'''
Copyright (c) 2011, Terrence Cole.
All rights reserved.
'''
from collections import OrderedDict
from millipede.hl.nodes.name import Name
from millipede.hl.nodes.nameref import NameRef
from millipede.hl.types.pydict import PyDictType
from millipede.lang.ast import AST
import itertools
import logging


class Scope:
	'''
	A symbol table.
	'''
	def __init__(self, owner:Name, *args, **kwargs):
		super().__init__(*args, **kwargs)

		self.symbols = OrderedDict()
		self.owner = owner

		# the topmost node of the control-flow-graph for this scope
		self.cfg = None

		# Records the scope's local "context" -- e.g. the lowlevel variable scope.
		# Set in visit_FuncDef during the time we visit our children.
		self.ctx = None

		# Keep track of how many labels we have used per prefix, so that we can
		#		ensure that each label we create is unique.
		self.labels = {}


	def lookup(self, name:str) -> Name:
		raise NotImplementedError("Every Scope type needs its own lookup routines.")


	def get_next_scope(self):
		'''
		Return the next highest scope to look in for names.
		Note: use this instead of owner.parent to skip class scopes.
		'''
		cur = self.owner.parent
		from millipede.hl.nodes.class_ import MpClass
		while isinstance(cur, MpClass):
			cur = cur.owner.parent
		return cur


	def has_name(self, name:str) -> bool:
		return name in self.symbols


	def owns_name(self, name:str) -> bool:
		return name in self.ownership


	def set_needs_closure(self):
		if self.owner.parent:
			self.owner.parent.set_needs_closure()


	def get_label(self, prefix):
		if prefix not in self.labels:
			self.labels[prefix] = itertools.count()
		return prefix + str(next(self.labels[prefix]))


	def add_symbol(self, name:str, init:object=None, ast:AST=None):
		if not init:
			init = Name(name, self, ast)
		self.symbols[name] = init
		return self.symbols[name]


	def set_reference(self, sym:Name):
		'''Add a reference to an existing name.  Like add reference, except that this ensures
			that the captured name _is_ a reference.  We use this when we know we are not
			the owner, but may be marked as the owner.  E.g. non-local definition before the
			symbol was created, etc.'''
		if sym.name in self.symbols and isinstance(self.symbols[sym.name], NameRef):
			return self.symbols[sym.name]
		self.symbols[sym.name] = NameRef(sym)
		return self.symbols[sym.name]



	def show(self, level=0):
		for sym in self.symbols.values():
			sym.show(level + 1)


	def create_instance(self, name:str):
		'''
		Instance the type with a name.  Sets the new instance on the 'inst' variable.
		'''
		self.inst = self.get_type()(name)

