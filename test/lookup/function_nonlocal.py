def foo():
	a = 0
	def bar():
		b = a
		print(b)
	bar()
foo()
#out: 0
