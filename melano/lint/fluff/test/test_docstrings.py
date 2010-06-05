'''
Tests for the docstrings fluff.
'''
__author__ = 'Terrence Cole <terrence@zettabytestorage.com>'


from .common import FluffTestBase
from ..docstrings import analyse
from melano.lint.messages import C0111, C0112


class TestLintDocstrings(FluffTestBase):
	def test_module_no_docstring(self):
		prog = '''# this is an initial comment
a = 2 * 2
'''
		with self.create('doc', prog) as unit:
			messages = list(analyse(unit))
		self.assertEqual(len(messages), 1)
		self.assertSameElements([C0111]*1, [m.__class__ for m in messages])


	def test_module_empty_docstring(self):
		prog = '''# this is an initial comment
""
'''
		with self.create('doc', prog) as unit:
			messages = list(analyse(unit))
		self.assertEqual(len(messages), 1)
		self.assertSameElements([C0112]*1, [m.__class__ for m in messages])


	def test_module_ok_docstring(self):
		prog = '''# this is an initial comment
"the docstring"
'''
		with self.create('doc', prog) as unit:
			messages = list(analyse(unit))
		self.assertEqual(len(messages), 0)


	def test_func_docstring(self):
		prog = '''
def foo(a:int, b:int, c:int) -> str:
	return 'foo'
'''
		with self.create('doc', prog) as unit:
			messages = list(analyse(unit))
		self.assertEqual(len(messages), 2)
		self.assertSameElements([C0111]*2, [m.__class__ for m in messages])


	def test_func_empty_docstring(self):
		prog = '''""
def foo(a:int, b:int, c:int) -> str:
	''
	return 'foo'
'''
		with self.create('doc', prog) as unit:
			messages = list(analyse(unit))
		self.assertEqual(len(messages), 2)
		self.assertSameElements([C0112]*2, [m.__class__ for m in messages])

		prog = '''
def foo(a:int, b:int, c:int) -> str:
	'hello world'
	return 'foo'
'''
		with self.create('doc', prog) as unit:
			messages = list(analyse(unit))
		self.assertEqual(len(messages), 1)
		self.assertSameElements([C0111]*1, [m.__class__ for m in messages])


	def test_class_no_docstring(self):
		prog = '''
class Foo:
	pass
'''
		with self.create('doc', prog) as unit:
			messages = list(analyse(unit))
		self.assertEqual(len(messages), 2)
		self.assertSameElements([C0111]*2, [m.__class__ for m in messages])


	def test_class_empty_docstring(self):
		prog = '''##
""
class Foo:
	""
	pass
'''
		with self.create('doc', prog) as unit:
			messages = list(analyse(unit))
		self.assertEqual(len(messages), 2)
		self.assertSameElements([C0112]*2, [m.__class__ for m in messages])


	def test_class_ok_docstring(self):
		prog = '''
class Foo:
	'hello world'
'''
		with self.create('doc', prog) as unit:
			messages = list(analyse(unit))
		self.assertEqual(len(messages), 1)
		self.assertSameElements([C0111]*1, [m.__class__ for m in messages])

