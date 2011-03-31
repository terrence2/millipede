class Foo:
	A = 'foo'
	print(A)
	del A
	try:
		print(A)
	except NameError as ex:
		print(str(ex))

#out: foo
#out: name 'A' is not defined
