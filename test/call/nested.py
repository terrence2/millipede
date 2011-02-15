a = "Hello"
def foo():
	b = ", World!"
	def bar():
		print(a + b)
	bar()
foo()
