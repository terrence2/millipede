with open('/dev/null', 'rb') as fp:
	print(fp.closed)
print(fp.closed)
#out: False
#out: True
