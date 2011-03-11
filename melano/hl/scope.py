'''
Copyright (c) 2011, Terrence Cole.
All rights reserved.
'''
from collections import OrderedDict
from melano.hl.name import Name
from melano.hl.nameref import NameRef
from melano.hl.types.pydict import PyDictType
import itertools
import logging


class Scope:
	'''
	A symbol table.
	'''
	def __init__(self, owner:Name):
		self.symbols = OrderedDict()
		self.owner = owner

		# will be set with the instance when we declare it
		self.ll = None

		# Records the scope's local "context" -- e.g. the lowlevel variable scope.
		# Set in visit_FuncDef during the time we visit our children.
		self.context = None

		# Keep track of how many labels we have used per prefix, so that we can
		#		ensure that each label we create is unique.
		self.labels = {}


	def lookup(self, name:str) -> Name:
		raise NotImplementedError("Every Scope type needs its own lookup routines.")


	def has_name(self, name:str) -> bool:
		return name in self.symbols


	def owns_name(self, name:str) -> bool:
		return name in self.ownership


	def has_closure(self) -> bool:
		for sym in self.symbols.values():
			if sym.scope:
				return True
		return False


	def get_label(self, prefix):
		if prefix not in self.labels:
			self.labels[prefix] = itertools.count()
		return prefix + str(next(self.labels[prefix]))


	def add_symbol(self, name:str, init:object=None):
		if not init:
			init = Name(name, self)
		self.symbols[name] = init
		return self.symbols[name]


	def add_reference(self, sym:Name):
		if sym.name in self.symbols:
			# already reffed, or we own the name
			return self.symbols[sym.name]
		self.symbols[sym.name] = NameRef(sym)
		return self.symbols[sym.name]


	def show(self, level=0):
		for sym in self.symbols.values():
			sym.show(level + 1)


	def get_type(self) -> type:
		'''
		Query the type list to find the most appropriate type for this name.
		'''
		return self.type


	def create_instance(self, name:str):
		'''
		Instance the type with a name.  Sets the new instance on the 'inst' variable.
		'''
		self.inst = self.get_type()(name)
