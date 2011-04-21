def foo():
	def bar(A):
		print(A)
		del A
		try:
			print(A)
		except UnboundLocalError as ex:
			print(str(ex))
	return bar

foo()('bar')
#out: bar
#out: local variable 'A' referenced before assignment
