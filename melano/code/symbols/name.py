'''
Copyright (c) 2010.  Terrence Cole
'''
from .symbol import Symbol

class Name(Symbol):
	def __init__(self, ast_name):
		super().__init__(str(ast_name), ast_name)
		self.type = None
