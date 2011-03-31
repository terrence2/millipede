A = 'foo'
B = 'bar'
print(A, B)
#out: foo bar

del A, B

try:
	print(A)
except NameError:
	print('deleted')
#out: deleted

try:
	print(B)
except NameError:
	print('deleted')
#out: deleted
