try:
	try:
		1 // 0
	except ZeroDivisionError:
		for i in range(5):
			print('ZDE')
			if i >= 2:
				break
		assert False
	finally:
		print('finally')
except AssertionError:
	print('assert')

#out: ZDE
#out: ZDE
#out: ZDE
#out: finally
#out: assert
