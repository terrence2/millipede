CURRENT = 0

def foo():
	a = CURRENT
	def _inner():
		print(a)
	return _inner

foo()()
#out: 0

CURRENT += 1
f = foo()
f()
#out: 1

CURRENT += 1
g = foo()
g()
#out: 2

f()
#out: 1
g()
#out: 2
