'''
Copyright (c) 2011, Terrence Cole.
All rights reserved.
'''
from melano.py.driver import PythonParserDriver

def test_comp():
	prog = '''new_callers[func] = tuple([i[0] + i[1] for i in zip(caller, new_callers[func])])\n\n'''
	driver = PythonParserDriver('data/grammar/python-3.1')
	driver.parse_string(prog)
