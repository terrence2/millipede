class A:
	def foo(self):
		print('A')

class B(A):
	def foo(self):
		super().foo()
		print('B')

B().foo()

#out: A
#out: B
