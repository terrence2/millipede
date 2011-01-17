'''
Tie together all of the different parts of the python parsing process and
expose a simple interface to parsing.
'''
__author__ = 'Terrence Cole <terrence@zettabytestorage.com>'

from .common.parser import PythonParser


class PythonParserDriver:
	'''
	Note: this driver is the only one that should need to worry explicitly
		about the version of python we are attempting to parse.
	'''
	def __init__(self, grammar_filename):
		self.grammar_filename = grammar_filename

		from .py3.grammar import PythonGrammar
		from .py3.tokenizer import PythonTokenizer
		from .py3.astbuilder import PythonASTBuilder

		self.parser = PythonParser(self.grammar_filename, PythonGrammar)
		self.tokenizer = PythonTokenizer(self.parser.grammar)
		self.builder = PythonASTBuilder(self.parser)


	def parse_string(self, content:str):
		tokens = self.tokenizer.tokenize(content)
		parse_tree = self.parser.parse(tokens)
		ast = self.builder.build(parse_tree)
		return ast

