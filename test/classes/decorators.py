#fail

def foo(cls):
	print('d')
	return cls

def bar(ty):
	print('a')
	def fn(cls):
		print('c')
		return cls
	return fn

@foo
@bar({int: str})
class Foo:
	print('b')

#out: a
#out: b
#out: c
#out: d
