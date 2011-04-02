'''
Copyright (c) 2011, Terrence Cole.
All rights reserved.
'''
from melano.c import ast as c
from melano.c.types.pyobject import PyObjectLL


class PyStringLL(PyObjectLL):
	@classmethod
	def bytes2c(cls, b):
		'''Reformats a python bytes to make it suitable for use as a C string constant.'''
		s = str(b)[2:-1]
		return s.replace('"', '\\x22')


	@classmethod
	def str2c(cls, s):
		'''Reformats a python string to make it suitable for use as a C string constant.'''
		#FIXME: r prefixed strings
		subs = [
			('\n', '\\n'),
			('\t', '\\t'),
			('\v', '\\v'),
			('"', '\\"')
		]
		for k, v in subs:
			s = s.replace(k, v)
		return s

	@classmethod
	def strlen(cls, s:str) -> int:
		'''Count the length of a c encoded string.'''
		cnt = 0
		for i, c in enumerate(s):
			if c == '\\':
				if len(s) > i + 1 and s[i + 1] == '\\':
					cnt += 1
			else:
				cnt += 1
		return cnt


	def new(self, ctx, py_init):
		# wchar_t is a signed type (!?!), so we need to do some checking here
		init = self.str2c(py_init)
		strlen = self.strlen(init)
		assert all(map(lambda x: ord(x) < 2 ** 31 and ord(x) >= 0, init)), 'Out of range character for wchar in: {}'.format(init)
		ctx.add(c.Assignment('=', c.ID(self.name), c.FuncCall(c.ID('PyUnicode_FromUnicode'), c.ExprList(
											c.Cast(c.PtrDecl(c.TypeDecl(self.name, c.IdentifierType('Py_UNICODE'))), c.Constant('string', init, prefix='L')),
											c.Constant('integer', strlen)))))
		self.fail_if_null(ctx, self.name)
