with open('/dev/zero', 'rb') as z, open('/dev/null', 'wb') as n:
	print(z.closed)
	print(n.closed)
print(z.closed)
print(n.closed)

#out: False
#out: False
#out: True
#out: True
