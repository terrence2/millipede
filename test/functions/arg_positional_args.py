#fail
def foo(a, b, c, d, e, f):
	print(a, b, c, d, e, f)
	return a + b + c + d + e + f
rv = foo(1, 2, 3, 4, 5, 6)
print(rv)
#out: 1 2 3 4 5 6
#out: 21
