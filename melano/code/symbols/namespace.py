'''
Map names to information about them.
'''
__author__ = 'Terrence Cole <terrence@zettabytestorage.com>'

from collections import OrderedDict
from .symbol import Symbol
from melano.parser.py3.ast import Name, AST


class Namespace(Symbol):
	def __init__(self, name:str or Name, ast_context:None or AST):
		'''
		Takes the unqualified name of this namespace.  This should be exactly
		equal to what this namespace is inserted as in the enclosing namespace.
		For lower levels, with an ast, this will be the ast.Name, whos str is 
		the str name.  A namespace is itself a symbol that has children.
		'''
		super().__init__(name, ast_context)
		self.symbols = OrderedDict()


	def add_symbol(self, namespace:Symbol):
		assert isinstance(namespace, Symbol)
		namespace.ast_node.symbol = namespace # create a backref
		self.symbols[namespace.name] = namespace


	def get_symbol(self, name:str) -> Symbol:
		assert isinstance(name, str)
		return self.symbols[name]


	def get_names(self) -> [str]:
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

