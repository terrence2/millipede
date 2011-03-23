try:
	try:
		print('a')
		assert 1 == 0
		print('b')
	finally:
		print('finally')
except AssertionError:
	print('assert')

#out: a
#out: finally
#out: assert
