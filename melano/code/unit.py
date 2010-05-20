'''
High level analytics for a single source file at a time.
'''
__author__ = 'Terrence Cole <terrence@zettabytestorage.com>'

import hashlib
import os.path


class ImageOutOfDate(Exception): pass


class MelanoCodeUnit:
	def __init__(self, config, filename):
		self.config = config
		self.filename = os.path.realpath(filename)
		self.cachefile = self.config.get_cachefile(self.filename)
		
		# load on demand
		self._ast = None		


	@property
	def ast(self):
		if not self._ast:
			try:
				self.thaw()
				return self._ast
			except (ImageOutOfDate, IOError):
				self.config.log.info("Parsing %s", os.path.basename(self.filename))
			parser = self.config.interpreters['3.1'].parser
			self._ast = parser.parse_file(self.filename)
		return self._ast


	def get_scopes(self):
		self.ast
		#from melano.parser.common.visitor import ASTVisitor
		#visitor = ASTVisitor()
		#visitor.visit(self.ast)


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



