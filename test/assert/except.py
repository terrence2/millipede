try:
	try:
		1 // 0
	except:
		print('a')
		assert 1 == 0
		print('b')
	finally:
		print('finally')
except AssertionError:
	print('except')

#out: a
#out: finally
#out: except
