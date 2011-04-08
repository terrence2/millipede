class Foo:
	def __init__(self):
		self.order = ['a', 'b', 'c']
		self.modules_by_path = {'a': 0, 'b': 1, 'c': 2}

	def foo(self):
		missing = {}
		records = {}
		visited = set()
		def _index(self):
			import sys
			nonlocal missing, records, visited
			for fn in self.order:
				if fn not in missing or missing[fn] > 0:
					mod = self.modules_by_path[fn]
					if fn not in missing:
						print("at", fn)
					else:
						print("repeat", fn)
					missing[fn] = 0 if fn in records else 1
					records[fn] = set()
					if 0 == missing[fn]:
						visited.add(mod)

		print('pass 1')
		_index(self)

		while sum(list(missing.values())) > 0:
			prior = sum(list(missing.values()))
			print('pass n')
			_index(self)
			cur = sum(list(missing.values()))
			if cur == prior:
				assert False

Foo().foo()
#out: pass 1
#out: at a
#out: at b
#out: at c
#out: pass n
#out: repeat a
#out: repeat b
#out: repeat c
