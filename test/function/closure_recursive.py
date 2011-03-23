def foo(a):
	if a == 0:
		return None
	def _inner():
		print(a)
	fn = foo(a - 1)
	if fn:
		fn()
	return _inner()
foo(5)
#out: 1
#out: 2
#out: 3
#out: 4
#out: 5
