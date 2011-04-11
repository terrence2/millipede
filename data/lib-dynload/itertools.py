
class chain:
	def __init__(self, *args): pass
	def __next__(self): pass

class count:
	def __init__(self, start=0, step=1): pass
	def __next__(self): return 0

class islice:
	def __init__(self, a, b, c=0, d=0): return ()
	def __next__(self): return 0

class repeat:
	def __init__(self, obj, times=0): pass
	def __next__(self): return 0
	def __iter__(self, *args): return 0

class starmap:
	def __init__(self, func, seq): pass
	def __next__(self): pass

def tee(iter, n=2): pass

