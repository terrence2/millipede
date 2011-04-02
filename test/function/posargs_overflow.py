def foo(a, b, c):
	print(a, b, c)
foo(0, 1, 2)
try:
	foo(0, 1, 2, 3, 4, 5)
except TypeError as ex:
	print('te', str(ex))
#out: 0 1 2
#out: te foo() takes exactly 3 positional arguments (6 given)

