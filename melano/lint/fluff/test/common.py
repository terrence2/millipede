'''
Base test setup, teardown, and utilities for all fluff tests.
'''
__author__ = 'Terrence Cole <terrence@zettabytestorage.com>'

from melano.code.unit import MelanoCodeUnit
from melano.config.config import MelanoConfig
from contextlib import contextmanager
import os
import tempfile
import unittest


class FluffTestBase(unittest.TestCase):
	def setUp(self):
		self.config = MelanoConfig()


	def tearDown(self):
		for fn in os.listdir('/tmp'):
			if fn.startswith('melinto-'):
				os.unlink('/tmp/' + fn)
	

	@contextmanager
	def create(self, name, code):
		fd, fn = tempfile.mkstemp('.py', 'melinto-' + name)
		with open(fd, 'wt', encoding='utf-8') as fp:
			fp.write(code)
		unit = MelanoCodeUnit(self.config, fn)
		yield unit
		os.unlink(fn)

