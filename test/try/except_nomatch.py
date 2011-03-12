def bar():
	try:
		return 1 / 0
	except IndexError:
		print('a')
	except KeyError:
		print('b')

def foo():
	try:
		return bar()
	except ZeroDivisionError:
		print('c')
	return 'd'

rv = foo()
#out: c

print(rv)
#out: d
