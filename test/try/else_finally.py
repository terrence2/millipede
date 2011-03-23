try:
	1 // 1
except:
	print('except')
else:
	print('else')
finally:
	print('finally')

try:
	1 // 0
except:
	print('except')
else:
	print('else')
finally:
	print('finally')


#out: else
#out: finally
#out: except
#out: finally
