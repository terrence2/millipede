'''
Discover and track what we know about a python language implementation.
'''
__author__ = 'Terrence Cole <terrence@zettabytestorage.com>'

from .python_version import PythonVersion
from melano.py.driver import PythonParserDriver


class PythonLanguage:
	def __init__(self, config, version:str):
		self.config = config
		self.version = PythonVersion(version)
		self.parser = PythonParserDriver(self.config, self.version)

