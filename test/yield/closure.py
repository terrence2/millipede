def foo(a):
	b = 1
	c = 2
	def _inner(d):
		yield a
		yield b
		yield c
		yield d
	return _inner
for i in foo(0)(3):
	print(i)
#out: 0
#out: 1
#out: 2
#out: 3
