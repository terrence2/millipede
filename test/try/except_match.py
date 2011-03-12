
def foo():
	raise NotImplementedError

def bar():
	raise NotImplementedError("This is an instance")

try:
	foo()
except IOError as ex:
	print(str(ex))
except NotImplementedError as ex:
	print(ex.__class__.__name__)
#out: NotImplementedError

try:
	bar()
except NotImplementedError as ex:
	print(str(ex))
except IOError as ex:
	print(str(ex))
#out: This is an instance
