fp = None
def foo():
	global fp
	with open('/dev/null', 'wb') as fp:
		print(fp.closed)
		return
foo()
print(fp.closed)

#out: False
#out: True
