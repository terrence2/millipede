a = 0
b = 'hello'


def bar():
	a = 1
	b = 'world'
bar()
print(a)
print(b)
#out: 0
#out: hello


def foo():
	global a, b
	a = 1
	b = 'world'
foo()
print(a)
print(b)
#out: 1
#out: world

