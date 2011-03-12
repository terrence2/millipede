def deco(fn):
	print('deco')
	def wrapper():
		print('a')
		rv = fn()
		print('b')
		return rv
	return wrapper

@deco
def foo():
	print('func')

foo()
#out: deco
#out: a
#out: func
#out: b
