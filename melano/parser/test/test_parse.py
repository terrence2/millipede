'''
High level tests.
'''
from melano.config.config import MelanoConfig
import unittest


class TestParse(unittest.TestCase):
	def test_classdef(self):
		toparse = '''
class Foo:
	bar = 0
	bas = 1
'''
		config = MelanoConfig()
		parser = config.interpreters['3.1'].parser
		ast = parser.parse_string(toparse)
		self.assertEqual(ast.body[1].__class__.__name__, 'ClassDef')
		self.assertEqual(ast.body[1].body[0].targets[0].id, 'bar')
		self.assertEqual(ast.body[1].body[1].targets[0].id, 'bas')

