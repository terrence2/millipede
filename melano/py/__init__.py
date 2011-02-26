'''
A parser for python source files.

Unlike the builtin python parser, this parser has 2 additional capabilities:
1) It should be able to parse supported versions of python, regardless of 
	what interpretter is running the parser.
2) It passes through full source-level information.  It includes the exact
	start and end information for all ast nodes by passing through direct
	refences to the low-level parse tree.

Parsing Process:
1) Tokenization
	We use python3's tokenize module, wrapped to provide symbol name lookup.
2) Parsing
	We generate a parse tree using pypy's pgen2 implementation.
3) AST
	We lower the parse tree to an ast using astbuilder, a heavily modified
	version of pypy's python2 ast builder.
'''
