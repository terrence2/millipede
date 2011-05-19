from contextlib import contextmanager

@contextmanager
def mycontextmgr():
	print('a')
	yield
	print('b')

foo = mycontextmgr()
with foo:
	pass

#out: a
#out: b
