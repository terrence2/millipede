'''
Tests for the annotations fluff.
'''
__author__ = 'Terrence Cole <terrence@zettabytestorage.com>'


from .common import FluffTestBase
from ..annotations import analyse
from melano.lint.messages import C0113, C0114


class TestLintAnnotations(FluffTestBase):
	def test_no_annotations(self):
		prog = '''
def foo(a, b, c):
	return 'foo'
'''
		with self.create('ann', prog) as unit:
			messages = list(analyse(unit))
		self.assertEqual(len(messages), 4)
		self.assertSameElements([C0113]*3 + [C0114], [m.__class__ for m in messages])


	def test_full_annotations(self):
		prog = '''
def foo(a:int, b:int, c:int) -> str:
	return 'foo'
'''
		with self.create('ann', prog) as unit:
			messages = list(analyse(unit))
		self.assertEqual(len(messages), 0)

