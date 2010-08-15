'''
Information about a name.
'''
__author__ = 'Terrence Cole <terrence@zettabytestorage.com>'




class Symbol:
	def __init__(self, name):
		self.name = name


	def insert(self, name:str, ref:object):
		print(name)
		self.symbols[name] = ref

