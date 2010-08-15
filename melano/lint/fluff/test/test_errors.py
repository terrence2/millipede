from .. import *

ERRORS = [g for g in globals() if g.startswith('E')]
print(ERRORS)

from melano.config.config import MelanoConfig
from melano.code.unit import MelanoCodeUnit
import os
import tempfile
import unittest


class TestLintErrors(unittest.TestCase):
	def setUp(self):
		self.config = MelanoConfig()


	def tearDown(self):
		for fn in os.listdir('/tmp'):
			if fn.startswith('melinto-'):
				os.unlink('/tmp/' + fn)
	

	def __create(self, name, code):
		fd, fn = tempfile.mkstemp('.py', 'melinto-' + name)
		with open(fd, 'wt', encoding='utf-8') as fp:
			fp.write(code)
		return fn


	
	def test_define_before_use(self):
		filename = self.__create('define_before_use_globals', '''
foo
foo=2''')
		unit = MelanoCodeUnit(self.config, filename)
		messages = globals()['E060_'].analyse(unit)
		self.assertEqual(len(messages), 1)
		self.assertEqual(messages[0].msg_name, 'E0601')

		filename = self.__create('define_before_use_locals', '''
def foo():
	foo
	bar
	bar=2
''')
		unit = MelanoCodeUnit(self.config, filename)
		messages = globals()['E060_'].analyse(unit)
		self.assertEqual(len(messages), 1)
		self.assertEqual(messages[0].msg_name, 'E0601')

		filename = self.__create('define_before_use_builtins', '''
foo=True; bas=False; bar=None
abs(foo); all(foo); any(foo); ascii(foo); bin(foo); bool(); bytearray(); 
bytes(); chr(foo); classmethod(foo); compile(foo, bas, bar); complex(foo, bar);
delattr(foo); dict(); dir(foo); divmod(foo, bar); enumerate(foo); eval(foo);
exec(foo); filter(foo, bar); float(); format(foo); frozenset(); 
getattr(foo, bar); globals(); hasattr(foo, bar); hash(foo); help(foo); hex();
id(foo); input(foo); int(); isinstance(foo, bar); issubclass(foo, bar); 
iter(foo); len(foo); list(); locals(); map(foo, bar); max(foo, bar); 
memoryview(); min(foo, bar); next(foo); object(); oct(foo); open(foo); ord(foo);
pow(foo, bar); print(); property(); range(foo, bar); repr(foo); reversed(foo);
round(foo); set(); setattr(foo, bar, bas); slice(foo); sorted(foo); 
staticmethod(foo); str(); sum(foo); super(); tuple(); type(foo, bar, bas);
vars(foo); zip(foo); __import__(foo);
''')
		unit = MelanoCodeUnit(self.config, filename)
		messages = globals()['E060_'].analyse(unit)
		self.assertEqual(len(messages), 0)

		filename = self.__create('define_before_use_delete', '''
del foo
foo=2''')
		unit = MelanoCodeUnit(self.config, filename)
		messages = globals()['E060_'].analyse(unit)
		self.assertEqual(len(messages), 1)
		self.assertEqual(messages[0].msg_name, 'E0601')


	def test_undefined(self):
		filename = self.__create('define', '''
foo''')
		unit = MelanoCodeUnit(self.config, filename)
		messages = globals()['E060_'].analyse(unit)
		self.assertEqual(len(messages), 1)
		self.assertEqual(messages[0].msg_name, 'E0602')

		filename = self.__create('undefined_delete', '''
del foo''')
		unit = MelanoCodeUnit(self.config, filename)
		messages = globals()['E060_'].analyse(unit)
		self.assertEqual(len(messages), 1)
		self.assertEqual(messages[0].msg_name, 'E0602')

