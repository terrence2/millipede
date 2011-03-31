def foo():
	A = 'foo'
	print(A)
	del A
	try:
		print(A)
	except UnboundLocalError as ex:
		print(str(ex))

foo()
#out: foo
#out: local variable 'A' referenced before assignment
