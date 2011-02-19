#fail
def foo(a:int, b:int, c:int, d:int, e:int, f:int) -> int:
	print(a, b, c, d, e, f)
	return a + b + c + d + e + f
rv = foo(1, 2, 3, 4, 5, 6)
print(rv)
#out: 1 2 3 4 5 6
#out: 21
