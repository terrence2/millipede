'''
A parser for python source files.

Unlike the builtin python parser, this parser has 2 additional capabilities:
1) It should (eventually) be able to parse any version of python from the
	running interpretter.
2) It passes through full source-level information.  It includes the exact
	start and end information for all ast nodes by passing through direct
	refences to the low-level parse tree.
'''
