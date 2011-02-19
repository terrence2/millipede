#fail
class Foo:
	class Bar:
		def foo(self):
			print('a')
	def foo(self):
		self.Bar().foo()
Foo().foo()
Foo().Bar().foo()
#out: a
#out: a
