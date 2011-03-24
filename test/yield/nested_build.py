def bar():
	yield 1
	yield 2
	yield 3

def foo():
	yield bar()

for gen in foo():
	for i in gen:
		print(i)

#out: 1
#out: 2
#out: 3
