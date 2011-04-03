# call the same generator multiple times
def foo(a=0, b=1, c=2, d=3):
	yield 'foo'

for s in foo('a', 'b', 'c', 'd'):
	print(s)
for s in foo('a', 'b', 'c', 'd'):
	print(s)
for s in foo('a', 'b', 'c', 'd'):
	print(s)
for s in foo('a', 'b', 'c', 'd'):
	print(s)
for s in foo('a', 'b', 'c', 'd'):
	print(s)

#out: foo
#out: foo
#out: foo
#out: foo
#out: foo
