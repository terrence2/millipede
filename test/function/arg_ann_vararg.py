def foo(*args:[int]) -> int:
	print(args)
	return sum(args)
rv = foo(1, 2, 3, 4)
print(rv)
#out: (1, 2, 3, 4)
#out: 10
print(foo.__annotations__['args'][0])
#out: <class 'int'>
