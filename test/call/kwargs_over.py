def foo(a, b, c, d):
	print(a, b, c, d)

A = {'a': 0, 'b': 1, 'c': 2, 'd': 3}
foo(4, 5, **A)
#skip_io
#returnvalue: 1
