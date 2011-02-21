def foo():
	bar()

def bar():
	baz()

def baz():
	fiz()

def fiz():
	raise NotImplementedError

foo()
