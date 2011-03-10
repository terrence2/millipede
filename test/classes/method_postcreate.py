class Foo:
	pass

def myfunc(a, b):
	print(type(a).__name__, b)

Foo.foo = myfunc
Foo.foo('a', 'b')
#out: str b
Foo().foo('hello')
#out: Foo hello

f = Foo()
f.bar = myfunc
f.bar('a', 'b')
#out: str b
