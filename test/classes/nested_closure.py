def foo(A):
	B = 'b'
	class Foo:
		FOO = 'foo'
		def meth_bar(self, a):
			b = 1
			def inner():
				print(A)
				print(B)
				print(self.FOO)
				print(a)
				print(b)
			return inner
	return Foo

cls = foo('a')
f = cls()
g = f.meth_bar(0)
g()
#out: a
#out: b
#out: foo
#out: 0
#out: 1
