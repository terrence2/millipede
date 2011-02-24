#attempt to make tmp vars collide
a = {}
a['foo'] = 'bar'
for k in a:
	f = a[k]
	print(f)
#out: bar
