def F():
	# locals is:
	# 0: [a, b]
	def foo():
		# locals is:
		# 1: [b]
		# 0: [a, b]
		nonlocal a
		b = 42
		def bar():
			# locals is:
			# 2: []
			# 1: [b]
			# 0: [a, b]
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
