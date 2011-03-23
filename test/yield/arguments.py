def foo(a, b, *, c=0, d=1):
	yield a
	yield b
	yield c
	yield d

print('defaults')
for i in foo(2, 3):
	print(i)
#out: defaults
#out: 2
#out: 3
#out: 0
#out: 1

print('kwargs')
for i in foo(0, 1, c='a', d='b'):
	print(i)
#out: kwargs
#out: 0
#out: 1
#out: a
#out: b

print('kwonlyargs')
for i in foo('a', 'b', 'c', 'd'):
	print(i)
#out: kwonlyargs
#out: a
#out: b
#out: 0
#out: 1
