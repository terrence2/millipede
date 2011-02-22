for _ in 'abc':
	with open('/dev/null', 'wb') as fp:
		print(fp.closed)
		break
print(fp.closed)
#out: False
#out: True
