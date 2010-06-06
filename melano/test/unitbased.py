'''
Adds to file based test by creating a unit.
'''
__author__ = 'Terrence Cole <terrence@zettabytestorage.com>'

from melano.code.unit import MelanoCodeUnit
from melano.config.config import MelanoConfig
from contextlib import contextmanager
from .filebased import FileBasedTest


class UnitBasedTest(FileBasedTest):
	def setUp(self):
		self.config = MelanoConfig()

	@contextmanager
	def create(self, name, code):
		with super().create(name, code) as fn:
			yield MelanoCodeUnit(self.config, fn)

