try:
	try:
		print('a')
		raise AssertionError
		print('b')
	except AssertionError:
		print('c')
		raise KeyError
		print('d')
except KeyError:
	print('keyerror')

#out: a
#out: c
#out: keyerror
