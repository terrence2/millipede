a = "Hello"
def foo():
	bar = lambda: print(a + b)
	b = ", World!"
	bar()
foo()
#out: Hello, World!
