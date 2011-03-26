SUPPRESS = True

class Ctx:
	def __enter__(self):
		print('a')

	def __exit__(self, exc, inst, tb):
		print('b')
		print(exc)
		if str(inst):
			print(str(inst))
		return SUPPRESS

try:
	with Ctx():
		raise NotImplementedError
except NotImplementedError:
	print('exc')
#out: a
#out: b
#out: <class 'NotImplementedError'>

SUPPRESS = False
try:
	with Ctx():
		raise NotImplementedError("test")
except NotImplementedError:
	print('exc')
#out: a
#out: b
#out: <class 'NotImplementedError'>
#out: test
#out: exc
