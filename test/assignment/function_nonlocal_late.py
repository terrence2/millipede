def foo():
	def bar():
		nonlocal a
		print(a)
	a = 1
	bar()
foo()
#out: 1
