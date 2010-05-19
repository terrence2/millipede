'''
Tie together all of the different parts of the python parsing process and
expose a simple interface to parsing.
'''
__author__ = 'Terrence Cole <terrence@zettabytestorage.com>'

from melano.config.python_version import PythonVersion
import os.path


class PythonParser:
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

		self.grammar = PythonGrammar()
		self.tokenizer = PythonTokenizer(self.grammar)

		#self.parser = PythonParser(self.version, self.grammar_filename)
		#self.builder = PythonAstBuilder(self.version)

