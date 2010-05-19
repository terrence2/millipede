'''
Discover and track what we know about a python language implementation.
'''
__author__ = 'Terrence Cole <terrence@zettabytestorage.com>'

from .python_version import PythonVersion
from melano.parser.driver import PythonParser


class PythonLanguage:
	def __init__(self, config, version:str):
		self.config = config
		self.version = PythonVersion(version)
		self.parser = PythonParser(self.config, self.version)

