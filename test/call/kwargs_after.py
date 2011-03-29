def foo(a, b, c, d):
	print(a, b, c, d)

A = {'b': 1, 'd': 3}
foo(0, c=2, **A)
#out: 0 1 2 3
