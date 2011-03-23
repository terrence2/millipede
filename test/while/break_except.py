i = 0
while i < 4:
	i += 1
	try:
		if i >= 3:
			1 // 0
	except ZeroDivisionError:
		print('ZDE')
		break
	finally:
		print('finally')
	print(i)

#out: finally
#out: 1
#out: finally
#out: 2
#out: ZDE
#out: finally
