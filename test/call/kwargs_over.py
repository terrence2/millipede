def foo(a, b, c, d):
	print(a, b, c, d)

A = {'e': 4}
try:
	foo(0, 1, 2, 3, **A)
except TypeError as ex:
	print(str(ex))
#out: foo() got an unexpected keyword argument 'e'

A = {'a': 0, 'b': 1, 'c': 2, 'd': 3}
try:
	foo(4, 5, **A)
except TypeError as ex:
	print(str(ex))
#out: foo() got multiple values for keyword argument 'a'
