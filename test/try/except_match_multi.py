def foo(a):
	if a:
		raise NotImplementedError('nie')
	else:
		raise AttributeError('ae')

for a in (True, False):
	try:
		foo(a)
	except (NotImplementedError, AttributeError) as e:
		print(str(e))
#out: nie
#out: ae
