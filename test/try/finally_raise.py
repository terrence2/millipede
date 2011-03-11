def foo():
	try:
		print('a')
		raise NotImplementedError
		print('b')
	finally:
		print('finally')
	print('do not show!')
foo()
#out: a
#out: finally
#returncode: 1
