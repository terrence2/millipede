try:
	try:
		1 // 0
	except KeyError:
		print('ke')
	else:
		print('else1')
except ZeroDivisionError:
	print('zde')
else:
	print('else2')
#out: zde
