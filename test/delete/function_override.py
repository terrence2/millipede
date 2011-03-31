A = 'bar'

def foo():
	A = 'foo'
	print(A)
	del A
	try:
		print(A)
	except UnboundLocalError:
		print('deleted')

foo()
#out: foo
#out: deleted
