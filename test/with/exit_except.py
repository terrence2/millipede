try:
	with open('/dev/null', 'rb') as fp:
		print(fp.closed)
		1 // 0
except ZeroDivisionError:
	print(fp.closed)

#out: False
#out: True
