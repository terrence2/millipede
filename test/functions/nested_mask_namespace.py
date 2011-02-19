a = 0
def foo():
	def bar():
		print(a)
	a = 1
	bar()
foo()
print(a)
#out: 1
#out: 0
