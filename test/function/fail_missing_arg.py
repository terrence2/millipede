def foo(a):
	print(a)

try:
	foo()
except TypeError:
	print("fail")

#out: fail
