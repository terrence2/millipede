'''
Definitions used by more than one linter.
'''
__author__ = 'Terrence Cole <terrence@zettabytestorage.com>'


BUILTINS = {
	'abs', 'all', 'any', 'ascii', 'bin', 'bool', 'bytearray',
	'bytes', 'chr', 'classmethod', 'compile', 'complex',
	'delattr', 'dict', 'dir', 'divmod', 'enumerate', 'eval',
	'exec', 'filter', 'float', 'format', 'frozenset',
	'getattr', 'globals', 'hasattr', 'hash', 'help', 'hex',
	'id', 'input', 'int', 'isinstance', 'issubclass',
	'iter', 'len', 'list', 'locals', 'map', 'max',
	'memoryview', 'min', 'next', 'object', 'oct', 'open', 'ord',
	'pow', 'print', 'property', 'range', 'repr', 'reversed',
	'round', 'set', 'setattr', 'slice', 'sorted',
	'staticmethod', 'str', 'sum', 'super', 'tuple', 'type',
	'vars', 'zip', '__import__', '__debug__', '__doc__',
	'__name__', '__package__', 'False', 'True', 'None'
}

KEYWORDS = {
	'class', 'finally', 'is', 'return',
	'continue', 'for', 'lambda', 'try',
	'def', 'from', 'nonlocal', 'while',
	'and', 'del', 'global', 'not', 'with',
	'as', 'elif', 'if', 'or', 'yield',
	'assert', 'else', 'import', 'pass',
	'break', 'except', 'in', 'raise'
}

