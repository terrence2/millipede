'''
Base test setup, teardown, and utilities for all fluff tests.
'''
__author__ = 'Terrence Cole <terrence@zettabytestorage.com>'

from melano.code.unit import MelanoCodeUnit
from melano.config.config import MelanoConfig
from melano.test.filebased import FileBasedTest
from contextlib import contextmanager
import os


class FluffTestBase(FileBasedTest):
	def setUp(self):
		self.config = MelanoConfig()


	def tearDown(self):
		for fn in os.listdir('/tmp'):
			if fn.startswith('melinto-'):
				os.unlink('/tmp/' + fn)
	

	@contextmanager
	def create(self, name, code):
		with super().create(name, code) as fn:
			yield MelanoCodeUnit(self.config, fn)

