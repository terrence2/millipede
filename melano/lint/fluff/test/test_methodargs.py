'''
Tests for method argument fluff.
'''
__author__ = 'Terrence Cole <terrence@zettabytestorage.com>'


from .common import FluffTestBase
from ..methodargs import analyse
from melano.lint.messages import C0201, E0201, C0202, E0202, C0203


class TestLintMethodArgs(FluffTestBase):
	def test_normal(self):
		prog = '''
class Foo:
	def bar(self, a, b, c):
		return 'foo'

	@classmethod
	def bas(cls, a, b, c):
		return 'foo'

	@staticmethod
	def bas(a, b, c):
		return 'foo'
'''
		with self.create('marg', prog) as unit:
			messages = list(analyse(unit))
		self.assertEqual(len(messages), 0)


	def test_method(self):
		prog = '''
class Foo:
	def bar(a, b, c):
		return 'foo'
	
	def baz():
		return 'foo'
'''
		with self.create('marg', prog) as unit:
			messages = list(analyse(unit))
		self.assertEqual(len(messages), 2)
		self.assertSameElements([C0201, E0201], [m.__class__ for m in messages])


	def test_class_method(self):
		prog = '''
class Foo:
	@classmethod
	def bar(a, b, c):
		return 'foo'

	@classmethod
	def baz():
		return 'foo'
'''
		with self.create('marg', prog) as unit:
			messages = list(analyse(unit))
		self.assertEqual(len(messages), 2)
		self.assertSameElements([C0202, E0202], [m.__class__ for m in messages])


	def test_static_method(self):
		prog = '''
class Foo:
	@staticmethod
	def bar(self, a, b, c):
		return 'foo'

	@staticmethod
	def bar(cls, a, b, c):
		return 'foo'
'''
		with self.create('marg', prog) as unit:
			messages = list(analyse(unit))
		self.assertEqual(len(messages), 2)
		self.assertSameElements([C0203] * 2, [m.__class__ for m in messages])

