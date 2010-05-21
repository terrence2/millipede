'''
A parser for python source files.

Unlike the builtin python parser, this parser has 2 additional capabilities:
1) It should (eventually) be able to parse any version of python from the
	running interpretter.
2) It passes through full source-level information.  It includes the exact
	start and end information for all ast nodes by passing through direct
	refences to the low-level parse tree.

Parsing Process:
1) Tokenization
	We run on python3, so we use the python3 tokenize module, wrapped to
	provide symbol name lookup.  When we move to provide python2 support,
	we will want to copy it's 2.7's tokenize module and run 2to3 on it.
2) Parsing
	We generate a parse tree using pypy's pgen2 implementation.
3) AST
	We lower the parse tree to an ast using py3.astbuilder, a heavily modified
	version of pypy's python2 ast builder.
'''
