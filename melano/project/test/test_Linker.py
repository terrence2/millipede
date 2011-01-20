'''
Copyright (c) 2011, Terrence Cole.
All rights reserved.
'''
from melano.parser.driver import PythonParserDriver
from melano.project.function import MelanoFunction
from melano.project.module import MelanoModule
from melano.project.passes.indexer import Indexer
from melano.project.passes.linker import Linker
from melano.project.project import MelanoProject
import unittest


class TestLinker(unittest.TestCase):
	def setUp(self):
		self.driver = PythonParserDriver('data/grammar/python-3.1')
		self.project = MelanoProject('test', [], [], [], [])

		self.tgt = MelanoModule('test/functions/empty.py')
		self.tgt.ast = self.driver.parse_string(self.tgt.source)
		indexer = Indexer(self.project, self.tgt)
		indexer.visit(self.tgt.ast)


	def test_import_from_func(self):
		mod = MelanoModule('test/import/from_func.py')
		mod.ast = self.driver.parse_string(mod.source)
		mod.refs['tgt'] = self.tgt
		linker = Linker(self.project, mod)
		linker.visit(mod.ast)
		self.assertTrue('foo' in mod.names)
		self.assertTrue(isinstance(mod.names['foo'], MelanoFunction))



