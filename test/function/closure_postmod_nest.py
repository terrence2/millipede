def F():
	def foo():
		nonlocal a
		b = 42
		def bar():
			print(a)
			print(b)
		a += 1
		return bar
	def baz():
		print(b)
	a = 0
	b = 1
	return foo, baz

foo, baz = F()
bar = foo()
bar()
baz()
#out: 1
#out: 42
#out: 1
foo()()
baz()
#out: 2
#out: 42
#out: 1
