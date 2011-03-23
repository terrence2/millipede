fp = None
for _ in 'abc':
	if fp is not None:
		print(fp.closed)
	with open('/dev/null', 'wb') as fp:
		print(fp.closed)
		continue
print(fp.closed)
#out: False
#out: True
#out: False
#out: True
#out: False
#out: True
