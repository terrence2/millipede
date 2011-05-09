import builtins as bltins

def mylen(a):
	return 42

foo = bltins

class C:
	def __init__(self):
		self.attr = [foo, 'foo']

C().attr[0].mylen = mylen
C().attr[0].len = mylen
