'''
Top-level wrapper for tokenization of python sources.
'''
__author__ = 'Terrence Cole <terrence@zettabytestorage.com>'

from io import StringIO
from tokenize import _tokenize


class PythonTokenizer:
	def __init__(self, grammar):
		self.grammar = grammar


	def tokenize(self, source:str) -> list:
		fp = StringIO(source)
		tokens = list(self.token_iter(fp.readline))
		return tokens


	def token_iter(self, readline):
		tokiter = _tokenize(readline, None)
		opmap = self.grammar.OPERATOR_MAP
		for tok in tokiter:
			ttype = opmap.get(tok.string, None)
			if ttype:
				yield tok._replace(type=ttype)
			else:
				yield tok

