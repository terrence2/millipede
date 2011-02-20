def foo():
	if A == 'a':
		print(1)
	elif A == 'b':
		print(2)
	elif A == 'c':
		print(3)
	elif A == 'd':
		print(4)
	else:
		print(5)

A = 'a'
foo()
A = 'b'
foo()
A = 'c'
foo()
A = 'd'
foo()
A = 'e'
foo()

#out: 1
#out: 2
#out: 3
#out: 4 
#out: 5
