'''
Tests for name usage fluff.
'''
__author__ = 'Terrence Cole <terrence@zettabytestorage.com>'


from .common import FluffTestBase
from ..name_use import analyse
from melano.lint.messages import \
	W0611, W0612, W0613, W0614, W0615, W0621, W0622, W0631, W0702, \
	E0601, E0602, E0603


class TestLintNameUse(FluffTestBase):
	def test_W0611_unused_import(self):
		prog = '''import os'''
		with self.create('name', prog) as unit:
			messages = list(analyse(unit))
		self.assertEqual(len(messages), 1)
		self.assertSameElements([W0611], [m.__class__ for m in messages])

		prog = '''import os.path'''
		with self.create('name', prog) as unit:
			messages = list(analyse(unit))
		self.assertEqual(len(messages), 1)
		self.assertSameElements([W0611], [m.__class__ for m in messages])

		prog = '''import os; os.listdir('/')'''
		with self.create('name', prog) as unit:
			messages = list(analyse(unit))
		self.assertEqual(len(messages), 0)

		prog = '''import os.path; os.path.join('/', 'foo')'''
		with self.create('name', prog) as unit:
			messages = list(analyse(unit))
		self.assertEqual(len(messages), 0)
		

	def test_W0612_unused_name(self):
		prog = '''a = 2 + 2'''
		with self.create('name', prog) as unit:
			messages = list(analyse(unit))
		self.assertEqual(len(messages), 1)
		self.assertSameElements([W0612], [m.__class__ for m in messages])

		prog = '''a = 2 + 2; print(a)'''
		with self.create('name', prog) as unit:
			messages = list(analyse(unit))
		self.assertEqual(len(messages), 0)

		prog = '''a = 2 + 2
def foo():
	print(a)'''
		with self.create('name', prog) as unit:
			messages = list(analyse(unit))
		self.assertEqual(len(messages), 0)

		prog = '''a = 2 + 2
class Foo:
	def foo(self):
		print(self, a)'''
		with self.create('name', prog) as unit:
			messages = list(analyse(unit))
		self.assertEqual(len(messages), 0)


	def test_W0613_unused_argument(self):
		prog = '''# unused argument
def foo(a):
	pass
foo(1)'''
		with self.create('name', prog) as unit:
			messages = list(analyse(unit))
		self.assertEqual(len(messages), 1)
		self.assertSameElements([W0613], [m.__class__ for m in messages])

		prog = '''# unused kwonly argument
def foo(*, a=1):
	pass
foo(a=1)'''
		with self.create('name', prog) as unit:
			messages = list(analyse(unit))
		self.assertEqual(len(messages), 1)
		self.assertSameElements([W0613], [m.__class__ for m in messages])

		prog = '''# unused star argument
def foo(*args):
	pass
foo(a=1)'''
		with self.create('name', prog) as unit:
			messages = list(analyse(unit))
		self.assertEqual(len(messages), 1)
		self.assertSameElements([W0613], [m.__class__ for m in messages])

		prog = '''# unused kwargs argument
def foo(**kwargs):
	pass
foo(a=1)'''
		with self.create('name', prog) as unit:
			messages = list(analyse(unit))
		self.assertEqual(len(messages), 1)
		self.assertSameElements([W0613], [m.__class__ for m in messages])

		prog = '''# no argument = no message
def foo():
	pass
foo()'''
		with self.create('name', prog) as unit:
			messages = list(analyse(unit))
		self.assertEqual(len(messages), 0)

		prog = '''# used argument = no message
def foo(a):
	print(a)
foo(1)'''
		with self.create('name', prog) as unit:
			messages = list(analyse(unit))
		self.assertEqual(len(messages), 0)


	def test_W0615_unused_with_var(self):
		prog = '''
from contextlib import contextmanager
@contextmanager
def foo(): yield 1
with foo as bar:
	pass'''
		with self.create('name', prog) as unit:
			messages = list(analyse(unit))
		self.assertEqual(len(messages), 1)
		self.assertSameElements([W0615], [m.__class__ for m in messages])

		prog = '''
from contextlib import contextmanager
@contextmanager
def foo(): yield 1
with foo as bar:
	print(bar)'''
		with self.create('name', prog) as unit:
			messages = list(analyse(unit))
		self.assertEqual(len(messages), 0)


	def test_E0601_use_before_define(self):
		prog = '''print(foo); foo = "hello world!"'''
		with self.create('name', prog) as unit:
			messages = list(analyse(unit))
		self.assertEqual(len(messages), 2)
		self.assertSameElements([E0601, W0612], [m.__class__ for m in messages])
		

	def test_E0602_undefined(self):
		prog = '''print(foo)'''
		with self.create('name', prog) as unit:
			messages = list(analyse(unit))
		self.assertEqual(len(messages), 1)
		self.assertSameElements([E0602], [m.__class__ for m in messages])


	def test_E0603_use_of_unbound_name(self):
		prog = '''
a = 2 + 2
del a
print(a)
a += 2
print(a)
'''
		with self.create('name', prog) as unit:
			messages = list(analyse(unit))
		self.assertEqual(len(messages), 2)
		self.assertSameElements([E0603] * 2, [m.__class__ for m in messages])


