
class chain:
	def __init__(self, *args): pass
	def __next__(self): pass

class combinations:
	def __init__(self, a, b): pass
	def __iter__(self): return self
	def __next__(self): return 0

class combinations_with_replacement:
	def __init__(self, a, b): pass
	def __iter__(self): return self
	def __next__(self): return 0

class compress:
	def __init__(self, a, b): pass
	def __iter__(self): return self
	def __next__(self): return 0

class count:
	def __init__(self, start=0, step=1): pass
	def __iter__(self): return self
	def __next__(self): return 0

class cycle:
	def __init__(self, a): pass
	def __iter__(self): return self
	def __next__(self): return 0

class dropwhile:
	def __init__(self, a, b): pass
	def __iter__(self): return self
	def __next__(self): return 0

class filterfalse:
	def __init__(self, a, b): pass
	def __iter__(self): return self
	def __next__(self): return 0

class groupby:
	def __init__(self, a, b=None): pass
	def __iter__(self): return self
	def __next__(self): return 0

class islice:
	def __init__(self, a, b, c=0, d=0): return ()
	def __iter__(self): return self
	def __next__(self): return 0

class permutations:
	def __init__(self, a, b=None): pass
	def __iter__(self): return self
	def __next__(self): return 0

class product:
	def __init__(self, *args): pass
	def __iter__(self): return self
	def __next__(self): return 0

class repeat:
	def __init__(self, obj, times=0): pass
	def __iter__(self): return self
	def __next__(self): return 0

class starmap:
	def __init__(self, func, seq): pass
	def __iter__(self): return self
	def __next__(self): return 0

class takewhile:
	def __init__(self, a, b): pass
	def __iter__(self): return self
	def __next__(self): return 0

class zip_longest:
	def __init__(self, *args, fillvalue=None): pass
	def __iter__(self): return self
	def __next__(self): return 0


def tee(iter, n=2): pass

