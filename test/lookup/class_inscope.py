class Foo():
	FOO = 0
	def a(self):
		print(FOO)

f = Foo()
try:
	f.a()
except:
	print('fail')
#out: fail
