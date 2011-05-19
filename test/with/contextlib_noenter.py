from contextlib import contextmanager

@contextmanager
def mycontextmgr():
	print('a')
	yield
	print('b')

print(mycontextmgr())

#this should simply not segfault
#skip_io
