'''
Copyright (c) 2011, Terrence Cole.
All rights reserved.
'''
from millipede.hl.types.pyobject import PyObjectType


class MalformedStringError(Exception):
	pass


class PyStringType(PyObjectType):
	ML_SINGLE = "'''"
	ML_DOUBLE = '"""'
	SINGLE = "'"
	DOUBLE = '"'

	PREFIXES = {'b', 'r', 'br', 'rb'}
	QUOTE_TYPES = [
		(ML_SINGLE, ML_SINGLE),
		(ML_DOUBLE, ML_DOUBLE),
		(SINGLE, SINGLE),
		(DOUBLE, DOUBLE),
	]
	for start, end in QUOTE_TYPES[:]:
		for prefix in PREFIXES:
			QUOTE_TYPES.append((prefix + start, end))


	@classmethod
	def dequote(cls, s):
		'''We get python strings as a literal string that contain the containing quotes.  We need to remove the outermost
			quote shell.'''
		for start, end in cls.QUOTE_TYPES:
			if s.startswith(start) and s.endswith(end):
				assert len(s) >= (len(start) + len(end)), 'why does this even parse?!?: {}'.format(s)
				return s[len(start):-len(end)]
		raise MalformedStringError(s)

