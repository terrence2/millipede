import random

def foo():
	try:
		if random.random() < 0.5:
			return
	finally:
		print('finally')
	print('a')
foo()

#out: finally
#out?: a
