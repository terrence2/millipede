
def foo():
	i = 0
	while i < 5:
		if i > 2:
			break
		print(i)
		i += 1
	else:
		print("broken")
foo()
#out: 0
#out: 1
#out: 2

def bar():
	i = 3
	while i < 5:
		print(i)
		i += 1
	else:
		print("success")
bar()
#out: 3
#out: 4
#out: success
