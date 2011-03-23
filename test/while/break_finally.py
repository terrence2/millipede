i = 0
while i < 4:
	i += 1
	try:
		if i >= 3:
			break
	finally:
		print('finally')
	print(i)

#out: finally
#out: 1
#out: finally
#out: 2
#out: finally
