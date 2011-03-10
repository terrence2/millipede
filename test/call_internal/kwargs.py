#fail
def foo(**kwargs):
	print(kwargs['a'], kwargs['b'], kwargs['c'])
foo(a=0, b=1, c=2)
#out: 0 1 2
