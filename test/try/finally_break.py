def foo():
	for i in range(2):
		try:
			print('a')
			if i == 1:
				break
		finally:
			print('finally')
		print('b')
	print('fin')
foo()
#out: a
#out: finally
#out: b
#out: a
#out: finally
#out: fin
