'''
Copyright (c) 2010.  Terrence Cole
'''
from melano.code.symbols.module import Module
from melano.parser.common.visitor import ASTVisitor

__author__ = 'Terrence Cole <terrence@zettabytestorage.com>'


class TypeExtractor(ASTVisitor):
	def __init__(self, module:Module):
		super().__init__()

		# the symbol database we will be writing to
		self.module = module
		self._context = [module]
