def foo():
	try:
		yield 'a'
		yield 1 // 0
		yield 'b'
	except:
		yield 'fail'
	finally:
		print('finally')

for i in foo():
	print(i)

#out: a
#out: fail
#out: finally

