#fail
def foo(*args):
	print(args)
	return sum(args)
rv = foo(1, 2, 3, 4)
print(rv)
#out: [1, 2, 3, 4]
#out: 10
