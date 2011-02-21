g = 'z'
def foo():
	global g
	for g in 'abc':
		pass
	print(g)
foo()
print(g)
#out: c
#out: c
