def foo(a=0, b=1, *, d=3, c=2, **kwargs):
	print(a, b, c, d, kwargs)
foo(a=0, b=1, c=2, d=3, e=4)
#out: 0 1 2 3 {'e': 4}
foo(e=4)
#out: 0 1 2 3 {'e': 4}
