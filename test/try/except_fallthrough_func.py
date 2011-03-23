def foo():
	try:
		1 // 0
	except KeyError:
		print('ke')

try:
	foo()
except ZeroDivisionError:
	print('zde')

#out: zde
