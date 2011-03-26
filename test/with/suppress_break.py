class Foo:
	def __enter__(self):
		print('enter')
	def __exit__(self, exc, inst, tb):
		print('exit')
		return True

for a in 'abc':
	print(a)
	with Foo():
		raise NotImplementedError
	break
print('end')
#out: a
#out: enter
#out: exit
#out: end
