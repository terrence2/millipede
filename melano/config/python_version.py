'''
Parse and stringify a canonical python version string.
'''
__author__ = 'Terrence Cole <terrence@zettabytestorage.com>'


class PythonVersion:
	def __init__(self, version:str):
		parts = version.split('.')
		self.major = int(parts[0])
		self.minor = int(parts[1])
	
	def __hash__(self):
		return hash(self.major + self.minor * 0.1)

	def __str__(self):
		return str(self.major) + '.' + str(self.minor)

