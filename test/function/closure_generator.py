
def foo(a, b, c):
	def _inner():
		yield a
		yield b
		yield c
	yield _inner

f = foo(1, 2, 3)
g = foo(4, 5, 6)

for gen in g:
	for i in gen():
		print(i)
#out: 4
#out: 5
#out: 6

for gen in f:
	for i in gen():
		print(i)
#out: 1
#out: 2
#out: 3
