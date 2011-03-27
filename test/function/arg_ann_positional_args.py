def foo(a:int, b:int, c:int, d:int, e:int, f:int) -> int:
	print(a, b, c, d, e, f)
	return a + b + c + d + e + f
rv = foo(1, 2, 3, 4, 5, 6)
print(rv)
#out: 1 2 3 4 5 6
#out: 21
print(foo.__annotations__['a'])
#out: <class 'int'>
print(foo.__annotations__['b'])
#out: <class 'int'>
print(foo.__annotations__['c'])
#out: <class 'int'>
print(foo.__annotations__['d'])
#out: <class 'int'>
print(foo.__annotations__['e'])
#out: <class 'int'>
print(foo.__annotations__['f'])
#out: <class 'int'>
print(foo.__annotations__['return'])
#out: <class 'int'>
