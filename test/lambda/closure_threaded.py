def foo(a, b, c):
	return lambda: print(a, b, c)
f = foo(1, 2, 3)
bg = lambda: foo(4, 5, 6)()

from threading import Thread
t = Thread(target=bg)
t.start()
t.join()
#out: 4 5 6

f()
#out: 1 2 3
