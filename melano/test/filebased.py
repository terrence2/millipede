'''
This test base class makes it easy to test against inlined file content.
'''
__author__ = 'Terrence Cole <terrence@zettabytestorage.com>'

from contextlib import contextmanager
import os
import tempfile
import unittest


class FileBasedTest(unittest.TestCase):
	def setUp(self):
		pass


	def tearDown(self):
		for fn in os.listdir('/tmp'):
			if fn.startswith('melinto-'):
				os.unlink('/tmp/' + fn)


	@contextmanager
	def create(self, name, code):
		fd, fn = tempfile.mkstemp('.py', 'melinto-' + name)
		with open(fd, 'wt', encoding='utf-8') as fp:
			fp.write(code)
		yield fn
		os.unlink(fn)

