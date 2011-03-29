def foo():
	global os
	import os
foo()
print(os.__name__)
#out: os
