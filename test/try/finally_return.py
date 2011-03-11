def foo():
	try:
		print('a')
		return
		print('b')
	finally:
		print('finally')
	print('do not show!')

foo()
#out: a
#out: finally
