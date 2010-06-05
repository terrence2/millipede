'''
Tests for the futures fluff.
'''
__author__ = 'Terrence Cole <terrence@zettabytestorage.com>'


from .common import FluffTestBase
from ..imports import analyse
from melano.lint.messages import W0401, W0410


class TestLintImports(FluffTestBase):
	def test_valid(self):
		prog = '''"docstring"
# comment
# comment
from __future__ import foo
from foo import bar
import bar
a = 2 + 2
'''
		with self.create('imp', prog) as unit:
			messages = list(analyse(unit))
		self.assertEqual(len(messages), 0)


	def test_star_import(self):
		prog = '''
from bar import *
def foo():
	from baz import *
'''
		with self.create('imp', prog) as unit:
			messages = list(analyse(unit))
		self.assertEqual(len(messages), 2)
		self.assertSameElements([W0401]*2, [m.__class__ for m in messages])


	def test_future_import(self):
		prog = '''
from bar import baz
from __future__ import foo
'''
		with self.create('imp', prog) as unit:
			messages = list(analyse(unit))
		self.assertEqual(len(messages), 1)
		self.assertSameElements([W0410], [m.__class__ for m in messages])

