A = {a: b for a in range(5) if a % 2 == 0 for b in range(5) if a == b and b % 2 == 0}
for e in A.items():
	print(e)
#out: (0, 0)
#out: (2, 2)
#out: (4, 4)
