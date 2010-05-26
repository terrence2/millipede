'''
Tests for the annotations fluff.
'''
__author__ = 'Terrence Cole <terrence@zettabytestorage.com>'


from .common import FluffTestBase
from ..annotations import analyse


class TestLintAnnotations(FluffTestBase):
	def test_annotations(self):
		prog = '''
def foo(a, b, c):
	return 'foo'
'''
		with self.create('ann', prog) as unit:
			messages = analyse(unit)
		self.assertEqual(len(messages), 4)

