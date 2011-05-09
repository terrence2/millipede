def mylen(a):
	return 42

A = [len, mylen]

for fn in A:
	print(fn(A))
#out: 2
#out: 42

A[0] = mylen

for fn in A:
	print(fn(A))
#out: 42
#out: 42

