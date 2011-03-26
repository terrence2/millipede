from contextlib import contextmanager

class Foo:
	@contextmanager
	def ctx(self, a, *, b=1):
		print(a)
		yield 'world'
		print(b)

with Foo().ctx(0):
	print('hello')
#out: 0
#out: hello
#out: 1

with Foo().ctx('a', b='b') as w:
	print(w)
#out: a
#out: world
#out: b
