'''
High level analytics for a single source file at a time.
'''
__author__ = 'Terrence Cole <terrence@zettabytestorage.com>'
from collections import Callable
import hashlib
import os.path


class ImageOutOfDate(Exception): pass


class MelanoCodeUnit:
	def __init__(self, config, filename:str):
		self.config = config
		self.raw_filename = filename
		self.filename = os.path.realpath(filename)
		self.cachefile = self.config.get_cachefile(self.filename)
		
		# load on demand
		self._ast = None


	def __get_property(self, name:str, onfail:Callable):
		'''Return the given property name, or call onfail if it's not present
			currrently and cannot be gotten from an existing source.'''
		if not getattr(self,name):
			try:
				self.thaw()
				return getattr(self, name)
			except (ImageOutOfDate, IOError):
				pass
			prop = onfail(self)
			setattr(self, name, prop)
			return prop
		return getattr(self, name)
		

	@property
	def ast(self):
		def get_ast(self):
			self.config.log.debug("Parsing: %s", os.path.basename(self.filename))
			parser = self.config.interpreters['3.1'].parser
			return parser.parse_file(self.filename)
		return self.__get_property('_ast', get_ast)

	
	def freeze(self):
		pass


	def thaw(self):
		with open(self.cachefile, 'rb') as fp:
			parts = pickle.load(fp)
		with open(self.filename, 'rb') as fp:
			raw_data = fp.read()
		real_md5 = hashlib.md5(raw_data).hexdigest()
		if real_md5 != parts['md5']:
			raise ImageOutOfDate()
		self._ast = parts['ast']




