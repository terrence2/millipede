def bar():
	yield 1
	yield 2
	yield 3

def foo():
	# this needs to call bar_builder from foo_runner and it needs to pass foo's current coro_context to the
	#		init for bar's generator
	for i in bar():
		yield i

for i in foo():
	print(i)

#out: 1
#out: 2
#out: 3
