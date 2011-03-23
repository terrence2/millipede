try:
	assert 0 == 1, 'incorrect'
except AssertionError as ex:
	print(ex.args[0])

#out: incorrect
