'''
Copyright (c) 2010.  Terrence Cole
'''
import melano.parser.py3.ast as ast

class Name:
	def __init__(self, node:ast.Name):
		self.node = node
		self.name = str(node)
		self.type = None
