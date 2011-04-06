foo = 'a' in 'foobar'
print(foo)
#out: True

class Foo:
	def foo(self):
		self.is_final = 'a' in 'foobar'
f = Foo()
f.foo()
print(f.is_final)
#out: True
