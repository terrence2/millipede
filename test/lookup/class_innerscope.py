class Foo:
	def a(self):
		print('a')
	b = a

Foo().a()
Foo().b()
#out: a
#out: a
