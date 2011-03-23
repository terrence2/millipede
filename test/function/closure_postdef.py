def foo():
	def _inner():
		print(a)
	a = 'foo'
	return _inner

foo()()
#out: foo
