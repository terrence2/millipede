'''
Copyright (c) 2011, Terrence Cole.
All rights reserved.
'''
from melano.parser.driver import PythonParserDriver
from melano.project.passes.typer import Typer
import unittest

class TestTyper(unittest.TestCase):
	def setUp(self):
		self.driver = PythonParserDriver('data/grammar/python-3.1')

	def test_assign_int(self):
		with open('test/assignment/ints.py', 'r') as fp:
			ast = self.driver.parse_string(fp.read())
		typer = Typer()
		typer.visit(ast)


