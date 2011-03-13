def deco1(fn):
	print('deco1')
	def wrapper():
		print('a')
		rv = fn()
		print('b')
		return rv
	return wrapper

def deco2(fn):
	print('deco2')
	def wrapper():
		print('A')
		rv = fn()
		print('B')
		return rv
	return wrapper

def deco3(ty):
	print('deco3')
	def deco3_inner(fn):
		print('deco3_inner')
		def wrapper():
			print('aa')
			rv = fn()
			print('bb')
			return rv
		return wrapper
	return deco3_inner

@deco1
@deco2
@deco3({int: str})
def foo():
	print('func')

foo()
#out: deco3
#out: deco3_inner
#out: deco2
#out: deco1
#out: a
#out: A
#out: aa
#out: func
#out: bb
#out: B
#out: b
