from threading import Lock
a = Lock()
with a:
	print(a.locked_lock())
print(a.locked_lock())
#out: True
#out: False
