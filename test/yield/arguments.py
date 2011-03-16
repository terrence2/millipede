def foo(a, b, *, c=0, d=1):
	yield a
	yield b
	yield c
	yield d

for i in foo(2, 3):
	print(i)
#out: 2
#out: 3
#out: 0
#out: 1

for i in foo(0, 1, c='a', d='b'):
	print(i)
#out: 2
#out: 3
#out: a
#out: b

for i in foo(0, 1, 2, 3):
	print(i)
#out: 0
#out: 1
#out: 2
#out: 3
