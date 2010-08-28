'''
Map names to information about them.
'''
__author__ = 'Terrence Cole <terrence@zettabytestorage.com>'

from .symbol import Symbol


class Namespace(Symbol):
	def __init__(self, name:str, ast_node):
		'''
		Takes the unqualified name of this namespace.  This should be exactly
		equal to what this namespace is inserted as in the enclosing namespace.
		'''
		super().__init__(name, ast_node)
		self.symbols = {}


	def add_symbol(self, namespace):
		self.symbols[str(namespace.name)] = namespace


	def get_symbol(self, name):
		return self.symbols[name]


	def get_names(self):
		return list(self.symbols.keys())


	def as_string_list(self, level:int=0):
		pad = '\t' * level
		parts = []
		for name, val in self.symbols.items():
			parts.append(pad + name)
			if isinstance(val, Namespace):
				parts += val.as_string_list(level + 1)
		return parts


	def as_string(self, level:int=0):
		return '\n'.join(self.as_string_list(level))

