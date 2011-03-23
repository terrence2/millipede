for i in range(5):
	try:
		if i < 3:
			1 // 0
	except ZeroDivisionError:
		print('ZDE')
		continue
	finally:
		print('finally')
	print(i)

#out: ZDE
#out: finally
#out: ZDE
#out: finally
#out: ZDE
#out: finally
#out: finally
#out: 3
#out: finally
#out: 4
