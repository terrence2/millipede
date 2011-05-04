import itertools

def _scope():
	def _inner():
		def foo():
			for i in range(5):
				yield i

		for i in itertools.islice(foo(), 3):
			print(i)

	for i in range(3):
		_inner()

_scope()

#out: 0
#out: 1
#out: 2

#out: 0
#out: 1
#out: 2

#out: 0
#out: 1
#out: 2


