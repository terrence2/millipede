'''
Tests for the returns fluff.
'''
__author__ = 'Terrence Cole <terrence@zettabytestorage.com>'


from .common import FluffTestBase
from ..returns import analyse
from melano.lint.messages import E0104, E0105


class TestLintReturns(FluffTestBase):
	def test_valid(self):
		prog = '''
def foo(a, b, c):
	return 'foo'

def foo(a, b, c):
	yield 'foo'
'''
		with self.create('ann', prog) as unit:
			messages = list(analyse(unit))
		self.assertEqual(len(messages), 0)
	
	def test_invalid(self):
		prog = '''
return 'foo'
yield 'foo'
class Foo:
	return 'foo'
	yield 'foo'
'''
		with self.create('ann', prog) as unit:
			messages = list(analyse(unit))
		self.assertEqual(len(messages), 4)
		self.assertSameElements([E0104, E0104, E0105, E0105], [m.__class__ for m in messages])


