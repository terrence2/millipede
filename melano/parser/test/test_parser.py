'''
Copyright (c) 2011, Terrence Cole.
All rights reserved.
'''
from melano.parser.driver import PythonParserDriver
import unittest

class TestParser(unittest.TestCase):
	'''Regression tests for know past problems.'''
	def setUp(self):
		self.driver = PythonParserDriver('data/grammar/python-3.1')

	def test_comp(self):
		prog = '''new_callers[func] = tuple([i[0] + i[1] for i in
                                           zip(caller, new_callers[func])])\n\n'''
		self.driver.parse_string(prog)
