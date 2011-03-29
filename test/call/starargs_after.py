def foo(a, b, c, d=0, e=1, f=2):
	print(a, b, c, d, e, f)

A = (0, 1, 2, 3)
foo(4, 5, *A)
#out: 4 5 0 1 2 3
