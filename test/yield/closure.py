def foo(a):
	b = 1
	c = 2
	def _inner():
		yield a
		yield b
		yield c
	return _inner
for i in foo(0):
	print(i)
#out: 0
#out: 1
#out: 2
