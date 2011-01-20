'''
Copyright (c) 2011, Terrence Cole.
All rights reserved.
'''
from melano.parser.driver import PythonParserDriver
from melano.project.module import MelanoModule
from melano.project.passes.indexer import Indexer
from melano.project.project import MelanoProject
import unittest


class TestIndexer(unittest.TestCase):
	def setUp(self):
		self.driver = PythonParserDriver('data/grammar/python-3.1')
		self.project = MelanoProject('test', [], [], [], [])
		self.project.name_to_path['os'] = '/os.py'
		self.project.name_to_path['xml'] = '/xml.py'
		self.project.modules['/os.py'] = 'os-module'
		self.project.modules['/xml.py'] = 'xml-module'


	def test_assign_int(self):
		mod = MelanoModule('test/assignment/ints.py')
		mod.ast = self.driver.parse_string(mod.source)
		indexer = Indexer(self.project, mod)
		indexer.visit(mod.ast)
		self.assertTrue('foo' in mod.names)
		self.assertEqual(mod.names['foo'], mod.names['foo'].node.hl)


	def test_import_basic(self):
		mod = MelanoModule('test/import/basic_module.py')
		mod.ast = self.driver.parse_string(mod.source)
		mod.refs['os'] = 'a'
		indexer = Indexer(self.project, mod)
		indexer.visit(mod.ast)
		self.assertEqual('a', mod.names['os'])


	def test_import_nest(self):
		mod = MelanoModule('test/import/basic_nest_module.py')
		mod.ast = self.driver.parse_string(mod.source)
		mod.refs['os.path'] = 'a'
		indexer = Indexer(self.project, mod)
		indexer.visit(mod.ast)
		self.assertEqual('os-module', mod.names['os'])


	def test_import_rename(self):
		mod = MelanoModule('test/import/basic_rename.py')
		mod.ast = self.driver.parse_string(mod.source)
		mod.refs['os'] = 'a'
		indexer = Indexer(self.project, mod)
		indexer.visit(mod.ast)
		self.assertEqual('a', mod.names['myos'])


	def test_import_multi_basic(self):
		mod = MelanoModule('test/import/multi_basic.py')
		mod.ast = self.driver.parse_string(mod.source)
		mod.refs['copy'] = 'a'
		mod.refs['contextlib'] = 'b'
		mod.refs['os'] = 'c'
		mod.refs['stat'] = 'd'
		indexer = Indexer(self.project, mod)
		indexer.visit(mod.ast)
		self.assertEqual(mod.names['copy'], 'a')
		self.assertEqual(mod.names['contextlib'], 'b')
		self.assertEqual(mod.names['os'], 'c')
		self.assertEqual(mod.names['stat'], 'd')


	def test_import_multi_nested(self):
		mod = MelanoModule('test/import/multi_nested.py')
		mod.ast = self.driver.parse_string(mod.source)
		mod.refs['xml.parsers.expat'] = 'a'
		mod.refs['xml.etree.ElementTree'] = 'b'
		indexer = Indexer(self.project, mod)
		indexer.visit(mod.ast)
		self.assertEqual('xml-module', mod.names['xml'])
		self.assertEqual('xml-module', mod.names['xml'])


	def test_import_multi_renamed(self):
		mod = MelanoModule('test/import/multi_renamed.py')
		mod.ast = self.driver.parse_string(mod.source)
		mod.refs['copy'] = 'a'
		mod.refs['contextlib'] = 'b'
		mod.refs['os'] = 'c'
		mod.refs['stat'] = 'd'
		indexer = Indexer(self.project, mod)
		indexer.visit(mod.ast)
		self.assertEqual('a', mod.names['mycopy'])
		self.assertEqual('b', mod.names['mycl'])
		self.assertEqual('c', mod.names['myos'])
		self.assertEqual('d', mod.names['mystat'])


	def test_class(self):
		mod = MelanoModule('test/classes/empty.py')
		mod.ast = self.driver.parse_string(mod.source)
		indexer = Indexer(self.project, mod)
		indexer.visit(mod.ast)
		self.assertTrue('Foo' in mod.names)


	def test_class_nested(self):
		mod = MelanoModule('test/classes/nested_empty.py')
		mod.ast = self.driver.parse_string(mod.source)
		indexer = Indexer(self.project, mod)
		indexer.visit(mod.ast)
		self.assertTrue('Foo' in mod.names)
		self.assertTrue('Bar' in mod.names['Foo'].names)


	def test_class_method(self):
		mod = MelanoModule('test/classes/method.py')
		mod.ast = self.driver.parse_string(mod.source)
		indexer = Indexer(self.project, mod)
		indexer.visit(mod.ast)
		self.assertTrue('Foo' in mod.names)
		self.assertTrue('foo' in mod.names['Foo'].names)
		self.assertTrue('self' in mod.names['Foo'].names['foo'].names)


	def test_class_attribute(self):
		mod = MelanoModule('test/classes/attribute.py')
		mod.ast = self.driver.parse_string(mod.source)
		indexer = Indexer(self.project, mod)
		indexer.visit(mod.ast)
		self.assertTrue('Foo' in mod.names)
		self.assertTrue('FOO' in mod.names['Foo'].names)


	def test_class_decorators(self):
		mod = MelanoModule('test/classes/decorators.py')
		mod.ast = self.driver.parse_string(mod.source)
		indexer = Indexer(self.project, mod)
		indexer.visit(mod.ast)
		self.assertTrue('Foo' in mod.names)


	def test_func(self):
		mod = MelanoModule('test/functions/empty.py')
		mod.ast = self.driver.parse_string(mod.source)
		indexer = Indexer(self.project, mod)
		indexer.visit(mod.ast)
		self.assertTrue('foo' in mod.names)


	def test_func_args(self):
		mod = MelanoModule('test/functions/arg_positional_args.py')
		mod.ast = self.driver.parse_string(mod.source)
		indexer = Indexer(self.project, mod)
		indexer.visit(mod.ast)
		self.assertTrue('foo' in mod.names)
		self.assertTrue('a' in mod.names['foo'].names)
		self.assertTrue('b' in mod.names['foo'].names)
		self.assertTrue('c' in mod.names['foo'].names)
		self.assertTrue('d' in mod.names['foo'].names)
		self.assertTrue('e' in mod.names['foo'].names)
		self.assertTrue('f' in mod.names['foo'].names)


	def test_func_vararg(self):
		mod = MelanoModule('test/functions/arg_vararg.py')
		mod.ast = self.driver.parse_string(mod.source)
		indexer = Indexer(self.project, mod)
		indexer.visit(mod.ast)
		self.assertTrue('foo' in mod.names)
		self.assertTrue('args' in mod.names['foo'].names)


	def test_func_kwonlyargs(self):
		mod = MelanoModule('test/functions/arg_kwonlyargs.py')
		mod.ast = self.driver.parse_string(mod.source)
		indexer = Indexer(self.project, mod)
		indexer.visit(mod.ast)
		self.assertTrue('foo' in mod.names)
		self.assertTrue('a' in mod.names['foo'].names)
		self.assertTrue('b' in mod.names['foo'].names)
		self.assertTrue('c' in mod.names['foo'].names)
		self.assertTrue('d' in mod.names['foo'].names)
		self.assertTrue('e' in mod.names['foo'].names)
		self.assertTrue('f' in mod.names['foo'].names)


	def test_func_kwarg(self):
		mod = MelanoModule('test/functions/arg_kwarg.py')
		mod.ast = self.driver.parse_string(mod.source)
		indexer = Indexer(self.project, mod)
		indexer.visit(mod.ast)
		self.assertTrue('foo' in mod.names)
		self.assertTrue('kwargs' in mod.names['foo'].names)


	def test_func_ann_args(self):
		mod = MelanoModule('test/functions/arg_ann_positional_args.py')
		mod.ast = self.driver.parse_string(mod.source)
		indexer = Indexer(self.project, mod)
		indexer.visit(mod.ast)
		self.assertTrue('foo' in mod.names)
		self.assertTrue('a' in mod.names['foo'].names)
		self.assertTrue('b' in mod.names['foo'].names)
		self.assertTrue('c' in mod.names['foo'].names)
		self.assertTrue('d' in mod.names['foo'].names)
		self.assertTrue('e' in mod.names['foo'].names)
		self.assertTrue('f' in mod.names['foo'].names)


	def test_func_ann_vararg(self):
		mod = MelanoModule('test/functions/arg_ann_vararg.py')
		mod.ast = self.driver.parse_string(mod.source)
		indexer = Indexer(self.project, mod)
		indexer.visit(mod.ast)
		self.assertTrue('foo' in mod.names)
		self.assertTrue('args' in mod.names['foo'].names)


	def test_func_ann_kwonlyargs(self):
		mod = MelanoModule('test/functions/arg_ann_kwonlyargs.py')
		mod.ast = self.driver.parse_string(mod.source)
		indexer = Indexer(self.project, mod)
		indexer.visit(mod.ast)
		self.assertTrue('foo' in mod.names)
		self.assertTrue('a' in mod.names['foo'].names)
		self.assertTrue('b' in mod.names['foo'].names)
		self.assertTrue('c' in mod.names['foo'].names)
		self.assertTrue('d' in mod.names['foo'].names)
		self.assertTrue('e' in mod.names['foo'].names)
		self.assertTrue('f' in mod.names['foo'].names)


	def test_func_ann_kwarg(self):
		mod = MelanoModule('test/functions/arg_ann_kwarg.py')
		mod.ast = self.driver.parse_string(mod.source)
		indexer = Indexer(self.project, mod)
		indexer.visit(mod.ast)
		self.assertTrue('foo' in mod.names)
		self.assertTrue('kwargs' in mod.names['foo'].names)


	def test_func_vars(self):
		mod = MelanoModule('test/functions/vars.py')
		mod.ast = self.driver.parse_string(mod.source)
		indexer = Indexer(self.project, mod)
		indexer.visit(mod.ast)
		self.assertTrue('foo' in mod.names)
		self.assertTrue('a' in mod.names['foo'].names)
		self.assertTrue('b' in mod.names['foo'].names)
		self.assertTrue('c' in mod.names['foo'].names)
		self.assertTrue('d' in mod.names['foo'].names)
		self.assertTrue('e' in mod.names['foo'].names)
		self.assertTrue('f' in mod.names['foo'].names)


	def test_func_nested_func(self):
		mod = MelanoModule('test/functions/nested_func.py')
		mod.ast = self.driver.parse_string(mod.source)
		indexer = Indexer(self.project, mod)
		indexer.visit(mod.ast)
		self.assertTrue('foo' in mod.names)
		self.assertTrue('bar' in mod.names['foo'].names)


	def test_func_nested_class(self):
		mod = MelanoModule('test/functions/nested_class.py')
		mod.ast = self.driver.parse_string(mod.source)
		indexer = Indexer(self.project, mod)
		indexer.visit(mod.ast)
		self.assertTrue('foo' in mod.names)
		self.assertTrue('Foo' in mod.names['foo'].names)


	def test_func_with(self):
		mod = MelanoModule('test/functions/with.py')
		mod.ast = self.driver.parse_string(mod.source)
		indexer = Indexer(self.project, mod)
		indexer.visit(mod.ast)
		self.assertTrue('foo' in mod.names)
		self.assertTrue('b' in mod.names['foo'].names)
		self.assertTrue('c' in mod.names['foo'].names)
