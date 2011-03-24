
def foo(a, b, c):
	def _runner():
		print(a)
		print(b)
		print(c)
	return _runner

f = foo(1, 2, 3)

def bg():
	g = foo(4, 5, 6)
	g()
from threading import Thread
t = Thread(target=bg)
t.start()
t.join()
#out: 4
#out: 5
#out: 6

f()
#out: 1
#out: 2
#out: 3
