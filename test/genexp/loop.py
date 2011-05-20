def foo():
	for i in range(6):
		if i % 2 == 0:
			yield tuple(j * j for j in range(i))

for v in foo():
	print(v)

#out: ()
#out: (0, 1)
#out: (0, 1, 4, 9)

