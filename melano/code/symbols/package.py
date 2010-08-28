'''
A directory that contains modules.
'''
__author__ = 'Terrence Cole <terrence@zettabytestorage.com>'

from .namespace import Namespace



class Package(Namespace):
	'''A collection of modules.'''
	def __init__(self, name:str):
		super().__init__(name, None)

