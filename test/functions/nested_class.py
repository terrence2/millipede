#fail
def foo():
	class Foo:
		print('a')
	return Foo()
	print('b')
foo()
#out: a
#out: b
