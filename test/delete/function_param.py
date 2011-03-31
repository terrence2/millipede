def foo(A):
	print(A)
	del A
	try:
		print(A)
	except UnboundLocalError as ex:
		print(str(ex))

foo('foo')
#out: foo
#out: local variable 'A' referenced before assignment
