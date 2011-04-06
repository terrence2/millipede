class Foo:
	def __init__(self, P):
		self.foo = {p: None for p in P}
f = Foo(['a', 'b', 'c'])
print(list(sorted(f.foo.items())))
#out: [('a', None), ('b', None), ('c', None)]
