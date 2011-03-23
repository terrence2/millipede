for i in range(5):
	try:
		if i < 3:
			continue
	finally:
		print('finally')
	print(i)

#out: finally
#out: finally
#out: finally
#out: finally
#out: 3
#out: finally
#out: 4
