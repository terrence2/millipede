class Foo:
	class Bar(Exception):
		pass

try:
	raise Foo.Bar
except Foo.Bar:
	print("catch")

#out: catch
