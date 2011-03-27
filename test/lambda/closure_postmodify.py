def F():
	def foo():
		nonlocal a
		a += 1
	bar = lambda: print(a)
	a = 0
	return foo, bar

foo, bar = F()

foo()
bar()
foo()
bar()
foo()
bar()
#out: 1
#out: 2
#out: 3

_, _ = F()

foo()
bar()
foo()
bar()
foo()
bar()
#out: 4
#out: 5
#out: 6
