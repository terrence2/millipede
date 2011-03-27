def F():
	def foo():
		nonlocal a
		b = 42
		bar = lambda: print(a, b)
		a += 1
		return bar
	baz = lambda: print(b)
	a = 0
	b = 1
	return foo, baz

foo, baz = F()
bar = foo()
bar()
baz()
#out: 1 42
#out: 1
foo()()
baz()
#out: 2 42
#out: 1
