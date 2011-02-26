'''
The PythonGrammar class encapsulates the knowledge that pypy's parser 
generator needs to generate a low-level parser for the python language and
that the low-level parser needs at runtime to parse the language.

This adds the SKIPTOKENS bits to support our additions to the parser and 
TOKEN_MAP as a convenience for printing useful info about parse trees.

NOTES for Melano:
	- Copied from pypy
	- Adds skiptokens to PythonGrammar
	- Adds TOKEN_MAP to PythonGrammar.
'''
from .pgen.parser import Grammar
from .tokens import python_tokens
from .tokens import python_opmap


class PythonGrammar(Grammar):
	KEYWORD_TOKEN = python_tokens["NAME"]
	SKIP_TOKENS = {
		python_tokens['COMMENT'],
		python_tokens['NL']}
	TOKENS = python_tokens
	OPERATOR_MAP = python_opmap

	TOKEN_MAP = {}
	for tok_str in TOKENS:
		TOKEN_MAP[TOKENS[tok_str]] = tok_str

