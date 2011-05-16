'''
Copyright (c) 2011, Terrence Cole.
All rights reserved.
'''
from melano.c import ast as c
from melano.c.types.pyobject import PyObjectLL


class PyStringLL(PyObjectLL):
	PY_LITERALS = {'newline', '\\', '\'', '"', 'a', 'b', 'f', 'n', 'r', 't', 'v', '\n'}
	PY_UNESCAPES = {
		'\\\\': '\\', 			# 	Backslash (\) 	 
		'\\\'': '\'', 			# 	Single quote (') 	 
		'\\"': '"', 			# 	Double quote (") 	 
		'\\a': '\a', 			# 	ASCII Bell (BEL) 	 
		'\\b': '\b', 			# 	ASCII Backspace (BS) 	 
		'\\f': '\f', 			#	ASCII Formfeed (FF) 	 
		'\\n': '\n', 			# 	ASCII Linefeed (LF) 	 
		'\\r': '\r', 			# 	ASCII Carriage Return (CR) 	 
		'\\t': '\t', 			# 	ASCII Horizontal Tab (TAB) 	 
		'\\v': '\v', 			# 	ASCII Vertical Tab (VT)
		'\\\n': '',
		'\\newline': '\n',
		#'\\ooo' 			#	Character with octal value ooo 	(1,3)
		#'\xhh' 				#	Character with hex value hh 	(2,3)

		# In Literals only!
		#'\N{name}' 	#	Character named name in the Unicode database 	 
		#'\uxxxx' 			#	Character with 16-bit hex value xxxx 	(4)
		#'\Uxxxxxxxx' #	Character with 32-bit hex value xxxxxxxx 	(5)
	}

	# Note: leaves out x and 0-9 which need special processing
	C_ESCAPE_CHARS = {'a', 'b', 'f', 'n', 'r', 't', 'v', '\'', '"', '\\', '?'}

	C_ESCAPES = {
		'\a': '\\a', # Bell (alert)
		'\b': '\\b', # Backspace
		'\f': '\\f', # Formfeed
		'\n': '\\n', # New line
		'\r': '\\r', # Carriage return
		'\t': '\\t', # Horizontal tab
		'\v': '\\v', # Vertical tab
		'\'': '\\\'', # Single quotation mark
		'"': '\\"', # Double quotation mark
		'\\': '\\\\', # Backslash
		'?': '\\?', # Literal question mark
		#'\ooo': ASCII character in octal notation
		#'\xhh': ASCII character in hexadecimal notation
		#'\xhhhh': Unicode character in hexadecimal notation if this escape sequence is used in a wide-character 
		#				constant or a Unicode string literal. 
	}


	@classmethod
	def name_to_c_string(cls, name):
		return cls._unapply_c_escapes(name)


	@classmethod
	def _apply_python_escapes(cls, s):
		'''Replace python escape sequences with their literal counterparts'''
		#FIXME: apply unicode, octal, and hex escapes here
		skip = 0
		out = []
		for i, c in enumerate(s):
			if skip > 0:
				skip -= 1
				continue
			if c == '\\':
				n = s[i + 1] if i + 1 < len(s) else '\0'
				if n in cls.PY_LITERALS:
					out.append(cls.PY_UNESCAPES['\\' + n])
					skip = 1
				else:
					out.append('\\\\')
			else:
				out.append(c)
		return ''.join(out)

		#for esc, lit in cls.PY_UNESCAPES.items():
		#	s = s.replace(esc, lit)


	@classmethod
	def _unapply_c_escapes(cls, s):
		'''Replace literals with thier C counterparts.'''
		out = []
		for c in s:
			if c in cls.C_ESCAPES:
				out.append(cls.C_ESCAPES[c])
			else:
				out.append(c)
		return ''.join(out)


	@classmethod
	def python_to_c_string(cls, s):
		'''Convert a python string to a c string.'''
		return cls._unapply_c_escapes(cls._apply_python_escapes(s))


	@classmethod
	def escape_c_string(cls, s):
		'''Take a string with arbitrary characters and formatting and represent it literally in C.'''
		return cls._unapply_c_escapes(cls._apply_python_escapes(s))


	@classmethod
	def strlen(cls, s:str) -> int:
		'''Count the length of a c encoded string.'''
		total = len(s)
		num_escapes = 0
		skip = 0
		for i, c in enumerate(s):
			if skip > 0:
				skip -= 1
				continue
			if c == '\\':
				n = s[i + 1] if i + 1 < len(s) else '\0'
				# ocal escapes are 3 digits
				if n in '01234567':
					for j in range(i + 2, i + 2 + 2):
						nn = s[i + j] if i + j < len(s) else '\0'
						assert nn in '01234567', 'Incomplete octal escape'
					num_escapes += 3
					skip = 3
				# hex escapes may be 2, 4, or 8 chars long, in addition to the initial x
				elif n == 'x':
					num_escapes += 1
					skip += 1
					for j in range(i + 2, i + 2 + 8):
						nn = s[i + 1] if i + 1 < len(s) else '\0'
						if nn not in '0123456789abcdefABCDEF':
							break
						num_escapes += 1
						skip += 1
				# otherwise we are probably a normal escape char
				if n in cls.C_ESCAPE_CHARS:
					num_escapes += 1
					skip = 1
		return total - num_escapes


	def new(self, py_init):
		super().new()
		# wchar_t is a signed type (!?!), so we need to do some checking here
		init = self.python_to_c_string(py_init)
		strlen = self.strlen(init)
		assert all(map(lambda x: ord(x) < 2 ** 31 and ord(x) >= 0, init)), 'Out of range character for wchar in: {}'.format(init)
		self.xdecref()
		self.v.ctx.add(c.Assignment('=', c.ID(self.name), c.FuncCall(c.ID('PyUnicode_FromUnicode'), c.ExprList(
											c.Cast(c.PtrDecl(c.TypeDecl(self.name, c.IdentifierType('Py_UNICODE'))), c.Constant('string', init, prefix='L')),
											c.Constant('integer', strlen)))))
		self.fail_if_null(self.name)

