A = [0, 1, 2, 3, 4, 5]
try:
	A[1::2] = []
except ValueError:
	print('ve')
else:
	print(A)
#out: ve
