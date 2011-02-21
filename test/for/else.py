#fail
for c in 'abc':
	if c == 'b':
		print('b')
		break
else:
	print("not present")
#out: b

for c in 'abc':
	pass
else:
	print('else')
#out: else
