def foo():
	return 'msg'

assert True, foo()
try:
	assert False, foo()
except AssertionError as ex:
	print(str(ex))

#out: msg
