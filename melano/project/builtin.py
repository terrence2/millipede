'''
Copyright (c) 2011, Terrence Cole.
All rights reserved.
'''

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
	'vars', 'zip', '__import__', 'False', 'True', 'None'
}
__CACHE = {}

def lookup_builtin(name):
	if name not in BUILTINS: return None
	if name not in __CACHE:
		__CACHE[name] = MelanoBuiltin(name)
	return __CACHE[name]


class MelanoBuiltin:
	def __init__(self, name):
		self.name = name

