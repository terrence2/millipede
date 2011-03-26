def foo():
	print('foo')
	return False

print(False and foo())
#out: False

print(foo() and foo())
#out: foo
#out: False
