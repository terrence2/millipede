import sys
def foo():
	try:
		print('a')
		raise NotImplementedError
		print('b')
	finally:
		print('finally')
	print('do not show!')

try:
	foo()
except:
	pass

#out: a
#out: finally
