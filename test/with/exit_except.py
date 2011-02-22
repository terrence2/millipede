try:
	with open('/dev/null', 'rb') as fp:
		print(fp.closed)
		raise NotImplementedError
except NotImplementedError:
	print(fp.closed)

#out: False
#out: True
