A = {(a, b) for a in range(5) if a % 2 == 0 for b in range(5) if a == b and b % 2 == 0}
print(A - {(0, 0), (2, 2), (4, 4)})
#out: set()
