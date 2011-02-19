#fail
def foo(**kwargs:{str: int}) -> int:
	print(kwargs['a'])
	print(kwargs['b'])
	return 10
rv = foo(b=43, a=42)
print(rv)
#out: 42
#out: 43
#out: 10
