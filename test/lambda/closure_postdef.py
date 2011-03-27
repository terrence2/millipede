def foo():
	_inner = lambda: print(a)
	a = 'foo'
	return _inner

foo()()
#out: foo
