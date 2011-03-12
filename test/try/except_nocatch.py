def foo():
	bar()

def bar():
	baz()

def baz():
	fiz()

def fiz():
	raise NotImplementedError

foo()


#Note: (1) we don't want to constrain our output to some exact match here, 
#		and (2) we expect our c linenos to be all over the place.
#skip_io
#returncode: 1
