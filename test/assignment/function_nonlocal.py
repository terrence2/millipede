#out: 0
#out: hello
#out: 1
#out: world
def foo():
	a = 0
	b = 'hello'

	def bar():
		a = 1
		b = 'world'
	bar()
	print(a)
	print(b)

	def baz():
		nonlocal a, b
		a = 1
		b = 'world'
	baz()
	print(a)
	print(b)

foo()
