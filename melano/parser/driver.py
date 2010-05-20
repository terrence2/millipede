'''
Tie together all of the different parts of the python parsing process and
expose a simple interface to parsing.
'''
__author__ = 'Terrence Cole <terrence@zettabytestorage.com>'

from melano.config.python_version import PythonVersion
from .common.parser import PythonParser
from .pgen.parser import ParseError
from tokenize import detect_encoding
import os.path


class PythonParserDriver:
	'''
	Note: this driver is the only one that should need to worry explicitly
		about the version of python we are attempting to parse.
	'''
	def __init__(self, config, version:PythonVersion):
		self.config = config
		self.version = version

		self.grammar_filename = os.path.join(self.config.data_dir, 
					'grammar', 'python-' + str(version))

		if self.version.major == 3:
			from .py3.grammar import PythonGrammar
			from .py3.tokenizer import PythonTokenizer
			from .py3.astbuilder import PythonASTBuilder

		self.parser = PythonParser(self.grammar_filename, PythonGrammar)
		self.tokenizer = PythonTokenizer(self.parser.grammar)
		self.builder = PythonASTBuilder(self.parser)


	def __read_file(self, filename):
		# read the file contents, obeying the python encoding marker
		try:
			with open(filename, 'rb') as fp:
				encoding, _ = detect_encoding(fp.readline)
		except SyntaxError as ex:
			raise ParseError('when detecting file encoding: {}'.format(str(ex)),
				None, str(ex), (0, 0), (2, 0), 0)
		try:
			with open(filename, 'rt', encoding=encoding) as fp:
				content = fp.read()
		except UnicodeDecodeError as ex:
			raise ParseError('invalid encoding: {}'.format(str(ex)),
				None, str(ex), (0, 0), (0, 0), 0)
		content += '\n\n'

		return content


	def parse_file(self, filename:str):
		content = self.__read_file(filename)
		return self.parse_string(content)


	def parse_string(self, content:str):
		tokens = self.tokenizer.tokenize(content)
		parse_tree = self.parser.parse(tokens)
		ast = self.builder.build(parse_tree)
		return ast

