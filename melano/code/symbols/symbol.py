'''
Information about a name.
'''
__author__ = 'Terrence Cole <terrence@zettabytestorage.com>'



class Symbol:
	def __init__(self, name:str, ast_node):
		self.name = name
		self.ast_node = ast_node


	def get_ast_node(self):
		return self.ast_node
