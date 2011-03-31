
def foo():
	yield
	yield
	yield

for i in foo():
	print(i)
#out: None
#out: None
#out: None
