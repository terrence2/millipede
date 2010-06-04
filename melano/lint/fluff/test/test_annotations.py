'''
Tests for the annotations fluff.
'''
__author__ = 'Terrence Cole <terrence@zettabytestorage.com>'


from .common import FluffTestBase
from ..annotations import analyse
from melano.lint.message import C0113, C0114


class TestLintAnnotations(FluffTestBase):
	def test_annotations(self):
		prog = '''
def foo(a, b, c):
	return 'foo'
'''
		with self.create('ann', prog) as unit:
			messages = list(analyse(unit))
		self.assertEqual(len(messages), 4)
		self.assertSameElements([C0113]*3 + [C0114], [m.__class__ for m in messages])


