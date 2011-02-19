#fail
def foo(*, a=0, b=1, c=2, d=3, e=4, f=5):
	print(a, b, c, d, e, f)
foo()
foo(a=6, b=7, c=8, d=9, e=10, f=11)
#out: 0 1 2 3 4 5
#out: 6 7 8 9 10 11
