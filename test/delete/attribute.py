class Foo:
	A = 42
	def foo(self):
		print(self.A)

f = Foo()

f.foo()
#out: 42

del Foo.A

try:
	f.foo()
except AttributeError as ex:
	print(str(ex))
#out: 'Foo' object has no attribute 'A'

try:
	del Foo.A
except AttributeError as ex:
	print(str(ex))
#out: A
