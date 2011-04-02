try:
	try:
		1 // 0
	except KeyError:
		print('ke')
except ZeroDivisionError:
	print('zde')
#out: zde
