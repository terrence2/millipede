'''
Tests for the generator fluff.
'''
__author__ = 'Terrence Cole <terrence@zettabytestorage.com>'


from .common import FluffTestBase
from ..generator import analyse
from melano.lint.messages import E0106


class TestLintGenerator(FluffTestBase):
	def test_ok_genfunc(self):
		prog = '''
def foo(a, b, c):
	return 'foo'

def bar(a, b, c):
	yield 'foo'
'''
		with self.create('gen', prog) as unit:
			messages = list(analyse(unit))
		self.assertEqual(len(messages), 0)
	
	
	def test_invalid_genfunc(self):
		prog = '''
def foo(a, b, c):
	yield 'foo'
	return 'foo'

def bar(a, b, c):
	return 'foo'
	yield 'foo'
'''
		with self.create('gen', prog) as unit:
			messages = list(analyse(unit))
		self.assertEqual(len(messages), 2)
		self.assertSameElements([E0106]*2, [m.__class__ for m in messages])

