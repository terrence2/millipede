A = 'bar'

def foo():
	def bar():
		A = 'foo'
		print(A)
		del A
		try:
			print(A)
		except UnboundLocalError:
			print('deleted')
	return bar

foo()()
#out: foo
#out: deleted
