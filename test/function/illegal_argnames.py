def foo(unsigned, long, *short, void=None, do=None, **double):
	print(unsigned, long, short, void, do, double)
foo(0, 1, 2, 3, 4, void=5, do=6, double=6)
#out: 0 1 (2, 3, 4) 5 6 {'double': 6}
#FIXME: need to remove void and do from the kwdict as we fill them into kwonly args
