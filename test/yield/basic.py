def foo():
	for i in range(5):
		yield i
	else:
		yield 'end'

for j in foo():
	print(j)
#out: 0
#out: 1
#out: 2
#out: 3
#out: 4
#out: end
