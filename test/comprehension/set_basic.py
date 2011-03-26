a = 'hello'
b = {a for a in range(4)}
print(a)
#out: hello
print(b - {0, 1, 2, 3})
#out: set()
