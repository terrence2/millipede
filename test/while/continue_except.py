i = 0
while i < 4:
	i += 1
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
#out: finally
#out: 3
#out: finally
#out: 4
