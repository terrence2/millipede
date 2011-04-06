def foo():
	A = {'foo': (0, 'a'), 'bar': (1, 'b'), 'baz': (2, 'c')}
	B = [(b, name) for name, (a, b) in A.items()]
	B.sort()
	print(B)
foo()
#out: [('a', 'foo'), ('b', 'bar'), ('c', 'baz')]
