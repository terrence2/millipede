'''
Information about a name.
'''
__author__ = 'Terrence Cole <terrence@zettabytestorage.com>'

from melano.parser.py3.ast import Name, AST


class Symbol:
	def __init__(self, name:Name, ast_context:AST):
		# ensure that we only get a string if there is no underlying node
		from .module import Module
		from .package import Package
		from .program import Program
		assert isinstance(name, Name) or isinstance(self, (Module, Package, Program))

		# keep the name as the str repr
		self.name = str(name)
		self.ast_node = name if isinstance(name, Name) else None
		self.ast_context = ast_context


	def get_ast_node(self):
		return self.ast_node
