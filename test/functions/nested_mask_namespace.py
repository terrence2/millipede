#prints:
#1
#0
a = 0
def foo():
	def bar():
		print(a)
	a = 1
	bar()
foo()
print(a)
