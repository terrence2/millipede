def foo():
	raise NotImplementedError

try:
	foo()
except NotImplementedError:
	print("a")
except:
	print("b")

#out: a
