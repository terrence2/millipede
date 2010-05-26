'''
High level analytics for a single source file at a time.
'''
__author__ = 'Terrence Cole <terrence@zettabytestorage.com>'
from .utils.symopmap import SymbolOpMapBuilder
import hashlib
import os.path


class ImageOutOfDate(Exception): pass


class MelanoCodeUnit:
	def __init__(self, config, filename):
		self.config = config
		self.raw_filename = filename
		self.filename = os.path.realpath(filename)
		self.cachefile = self.config.get_cachefile(self.filename)
		
		# load on demand
		self._ast = None
		self._opmap = None


	def __get_property(self, name, onfail):
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


	@property
	def opmap(self):
		def get_opmap(self):
			self.config.log.debug("Building OpMap: %s", os.path.basename(self.filename))
			visitor = SymbolOpMapBuilder()
			visitor.visit(self.ast)
			return visitor.opmap
		return self.__get_property('_opmap', get_opmap)


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




