'''
Tie together all of the different parts of the python parsing process and
expose a simple interface to parsing.
'''
__author__ = 'Terrence Cole <terrence@zettabytestorage.com>'

from melano.config.python_version import PythonVersion
from .common.parser import PythonParser
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

		self.parser = PythonParser(self.grammar_filename, PythonGrammar)
		self.tokenizer = PythonTokenizer(self.parser.grammar)

		#self.parser = PythonParser(self.version, self.grammar_filename)
		#self.builder = PythonAstBuilder(self.version)


	def parse(self, content:str):
		tokens = self.tokenizer.tokenize(content)
		parse_tree = self.parser.parse(tokens)
		
		return parse_tree

