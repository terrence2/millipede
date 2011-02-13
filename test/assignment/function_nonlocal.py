def foo():
	a = 0
	b = 'hello'
	def bar():
		nonlocal a, b
		a = 1
		b = 'world'
