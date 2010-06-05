'''
Tests for the annotations fluff.
'''
__author__ = 'Terrence Cole <terrence@zettabytestorage.com>'


from .common import FluffTestBase
from ..classinit import analyse
from melano.lint.messages import E0100, E0101


class TestLintClassInit(FluffTestBase):
	def test_normal(self):
		prog = '''
class Foo:
	def __init__(self):
		pass
	
	def foo(self):
		yield 'foo'
	
	def bar(self):
		return 'foo'
'''
		with self.create('cls', prog) as unit:
			messages = list(analyse(unit))
		self.assertEqual(len(messages), 0)


	def test_generator(self):
		prog = '''
class Foo:
	def __init__(self):
		yield 'foo'
'''
		with self.create('cls', prog) as unit:
			messages = list(analyse(unit))
		self.assertEqual(len(messages), 1)
		self.assertSameElements([E0100], [m.__class__ for m in messages])


	def test_returns(self):
		prog = '''
class Foo:
	def __init__(self):
		return 'foo'
'''
		with self.create('ann', prog) as unit:
			messages = list(analyse(unit))
		self.assertEqual(len(messages), 1)
		self.assertSameElements([E0101], [m.__class__ for m in messages])

