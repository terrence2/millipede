def foo():
	def bar():
		nonlocal a

		a |= 12
		print(a)
		a |= 2
		print(a)
		#out: 12
		#out: 14

		a ^= 10
		print(a)
		#out: 4

		a &= 6
		print(a)
		a &= 2
		print(a)
		#out: 4
		#out: 0

		a += 42
		print(a)
		#out: 42

		a -= 43
		print(a)
		#out: -1

		a *= 25
		print(a)
		#out: -25

		a /= 5
		print(a)
		#out: -5.0

		a //= 2
		print(a)
		#out: -3.0

		a = -5
		a //= 2
		print(a)
		#out: -3

		a **= 3
		print(a)
		#out: -27

		a *= -1
		a %= 7
		print(a)
		#out: 6

		a = -27
		a %= 7
		print(a)
		#out: 1

	a = 4
	return bar

foo()()
#out: 12
#out: 14
#out: 4
#out: 4
#out: 0
#out: 42
#out: -1
#out: -25
#out: -5.0
#out: -3.0
#out: -3
#out: -27
#out: 6
#out: 1
