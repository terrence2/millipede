from contextlib import contextmanager


@contextmanager
def foo(a, b, c):
	print(a)
	with bar(b, c):
		yield

@contextmanager
def bar(b, c):
	print(b)
	with baz(c):
		yield

@contextmanager
def baz(c):
	print(c)
	yield


with foo(0, 1, 2):
	print('hello')

#out: 0
#out: 1
#out: 2
#out: hello
