try:
	try:
		print('a')
		raise AssertionError
		print('b')
	except AssertionError:
		print('c')
		raise
		print('d')
except AssertionError:
	print('assertion')

#out: a
#out: c
#out: assertion

