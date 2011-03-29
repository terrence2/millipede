#NOTE: we have no length for a generator... we need to use only sequence protocol for * unpacking
def args():
	for i in range(4):
		yield i

def foo(a, b, c, d, e, f):
	print(a, b, c, d, e, f)

foo(4, 5, *args())
#out: 4 5 0 1 2 3
