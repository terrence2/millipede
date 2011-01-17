'''
Copyright (c) 2011, Terrence Cole.
All rights reserved.
'''
from melano.parser.driver import PythonParserDriver
from melano.project.module import MelanoModule
from melano.project.passes.namer import Namer
import unittest

class TestNamer(unittest.TestCase):
	def setUp(self):
		self.driver = PythonParserDriver('data/grammar/python-3.1')


	def test_class(self):
		mod = MelanoModule('test/classes/empty.py')
		mod.ast = self.driver.parse_string(mod.source)
		namer = Namer(mod)
		namer.visit(mod.ast)
		self.assertTrue('Foo' in mod.names)


	def test_class_nested(self):
		mod = MelanoModule('test/classes/nested_empty.py')
		mod.ast = self.driver.parse_string(mod.source)
		namer = Namer(mod)
		namer.visit(mod.ast)
		self.assertTrue('Foo' in mod.names)
		self.assertTrue('Foo.Bar' in mod.names)
		self.assertTrue('Bar' in mod.names['Foo'].names)


	def test_function(self):
		mod = MelanoModule('test/functions/empty.py')
		mod.ast = self.driver.parse_string(mod.source)
		namer = Namer(mod)
		namer.visit(mod.ast)
		self.assertTrue('foo' in mod.names)




