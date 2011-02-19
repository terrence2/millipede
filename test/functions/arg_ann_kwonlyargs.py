#fail
def foo(*, a:int=0, b:int=1, c:int=2, d:int=3, e:int=4, f:int=5) -> int:
	print(a, b, c, d, e, f)
foo()
foo(a=6, b=7, c=8, d=9, e=10, f=11)
#out: 0 1 2 3 4 5
#out: 6 7 8 9 10 11
