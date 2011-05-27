'''
Wraps pypy's low-level pgen and provides some supporting infrastructure.  
This is original to millipede, but based heavily on the equivalent class in pypy.
'''
from .pgen.metaparser import ParserGenerator
from .pgen.parser import Parser, Grammar, Node
import io


class PythonParser(Parser):
	def __init__(self, grammar_file:str, grammar_cls:Grammar):
		# build a parser generator for the provided grammar
		with open(grammar_file, 'rt', encoding='utf-8') as fp:
			grammar_source = fp.read()
		pgen = ParserGenerator(grammar_source)
		pgen.start_symbol = 'file_input'

		# build a grammar with the generator and the grammar symbols
		gram = pgen.build_grammar(grammar_cls)

		# pass on the grammar to the real parser
		super().__init__(gram)


	def parse(self, tokens:list) -> Node:
		self.prepare()
		for tok in tokens:
			rv = self.add_token(tok.type, tok.string, tok.start, tok.end, tok.line)
			if rv is True:
				out = self.root
				self.root = None
				return out

