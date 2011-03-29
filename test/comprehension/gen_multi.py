A = ((a, b) for a in range(5) if a % 2 == 0 for b in range(5) if a == b and b % 2 == 0)
for a in A:
	print(a)
#out: (0, 0)
#out: (2, 2)
#out: (4, 4)
