'''
High level tests.
'''
from melano.config.config import MelanoConfig
import unittest


class TestParse(unittest.TestCase):
	def setUp(self):
		self.config = MelanoConfig()
		self.parser31 = self.config.interpreters['3.1'].parser


	def test_classdef(self):
		toparse = '''
class Foo:
	bar = 0
	bas = 1
'''
		ast = self.parser31.parse_string(toparse)
		self.assertEqual(ast.body[0].__class__.__name__, 'ClassDef')
		self.assertEqual(ast.body[0].body[0].targets[0].id, 'bar')
		self.assertEqual(ast.body[0].body[1].targets[0].id, 'bas')


	def test_suite(self):
		toparse = '''
if 1: break
if 2: pass; break
if 3:
	break
if 4:
	pass
	break
'''
		ast = self.parser31.parse_string(toparse)
		self.assertEqual(ast.body[0].__class__.__name__, 'If')
		self.assertEqual(ast.body[1].__class__.__name__, 'If')
		self.assertEqual(ast.body[2].__class__.__name__, 'If')
		self.assertEqual(ast.body[3].__class__.__name__, 'If')

		self.assertEqual(ast.body[0].body[0].__class__.__name__, 'Break')
		self.assertEqual(ast.body[1].body[0].__class__.__name__, 'Pass')
		self.assertEqual(ast.body[1].body[1].__class__.__name__, 'Break')
		self.assertEqual(ast.body[2].body[0].__class__.__name__, 'Break')
		self.assertEqual(ast.body[3].body[0].__class__.__name__, 'Pass')
		self.assertEqual(ast.body[3].body[1].__class__.__name__, 'Break')

