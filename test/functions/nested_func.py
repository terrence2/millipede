a = 0
def foo():
	b = 1
	def bar():
		c = 2
		def baz():
			print(a)
			print(b)
			print(c)
		baz()
	bar()
foo()
#out: 0
#out: 1
#out: 2
