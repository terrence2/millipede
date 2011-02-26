'''
Copyright (c) 2011, Terrence Cole.
All rights reserved.
'''
from collections import OrderedDict
from melano.c.types.lltype import LLType
from melano.c.types.pydict import PyDictType
from melano.hl.name import Name
from melano.hl.nameref import NameRef


class Scope:
	'''
	A symbol table.
	'''
	def __init__(self, owner:Name):
		self.symbols = OrderedDict()
		self.owner = owner

		# the name of the global variable used to reference this scope
		self.ll_scope = None

		# the name of the low-level function used to build/run the scope 
		self.ll_runner = None

		# scopes can have a single type, and it is almost only a simple PyDictType
		self.type = PyDictType

		# will be set with the instance when we declare it
		self.inst = None

		# Records the scope's local "context" -- e.g. the lowlevel variable scope.
		# Set in visit_FuncDef during the time we visit our children.
		self.context = None


	def lookup(self, name:str) -> Name:
		try:
			return self.symbols[name]
		except KeyError:
			if self.owner.parent:
				return self.owner.parent.lookup(name)
			raise


	def has_name(self, name:str) -> bool:
		return name in self.symbols


	def owns_name(self, name:str) -> bool:
		return name in self.ownership


	def has_closure(self) -> bool:
		for sym in self.symbols.values():
			if sym.scope:
				return True
		return False


	def add_symbol(self, name:str, init:object=None):
		self.symbols[name] = Name(name, self)
		return self.symbols[name]


	def add_reference(self, sym:Name):
		if sym.name in self.symbols:
			# already reffed, or we own the name
			return self.symbols[sym.name]
		self.symbols[sym.name] = NameRef(sym)
		return self.symbols[sym.name]


	def show(self, level=0):
		for name in self.symbols:
			self.symbols[name].show(level + 1)


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
