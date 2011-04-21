def foo(A):
	def bar():
		nonlocal A
		print(A)
		del A
		try:
			print(A)
		except NameError as ex:
			print(str(ex))
	return bar

foo('foo')()
#out: foo
#out: local variable 'A' referenced before assignment
