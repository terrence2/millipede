class mycontext:
	def __init__(self):
		self.foo = 1
	def __enter__(self):
		print('enter')
		self.foo += 1
		return self
	def __exit__(self, exc_type, exc_value, traceback):
		self.foo += 1
		print('exit')
		return False # do not supress exceptions

with mycontext() as ctx:
	print(ctx.foo)
print(ctx.foo)
#out: enter
#out: 2
#out: exit
#out: 3

try:
	with mycontext() as ctx:
		print(ctx.foo)
		raise NotImplementedError
except NotImplementedError:
	print(ctx.foo)
#out: enter
#out: 2
#out: exit
#out: 3
