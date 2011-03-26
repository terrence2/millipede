def foo():
	print('foo')
	return True

print(True or foo())
#out: True

print(foo() or foo())
#out: foo
#out: True
