from contextlib import contextmanager

@contextmanager
def mycontextmgr():
	print('a')
	yield 'hello'
	print('b')

with mycontextmgr() as ctx:
	print(ctx)

#out: a
#out: hello
#out: b
