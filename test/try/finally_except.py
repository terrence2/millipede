
try:
	print('a')
	print(1 / 1)
	print('b')
finally:
	print('finally')
#out: a
#out: 1.0
#out: b
#out: finally

try:
	print('a')
	print(1 / 0)
	print('b')
finally:
	print('finally')
#out: a
#out: finally

print('do not show this!')

#skip_io
#returncode: 1
