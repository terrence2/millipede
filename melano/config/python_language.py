'''
Discover and track what we know about a python language implementation.
'''
__author__ = 'Terrence Cole <terrence@zettabytestorage.com>'


class PythonVersion:
	def __init__(self, version:str):
		parts = version.split('.')
		self.major = int(parts[0])
		self.minor = int(parts[1])
	
	def __hash__(self):
		return hash(self.major + self.minor * 0.1)


class PythonLanguage:
	def __init__(self, config, version:str):
		self.config = config
		self.version = PythonVersion(version)

