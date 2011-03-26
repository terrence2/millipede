a = 'hello'
b = {a: a for a in range(4)}
print(a)
print(b)
#out: hello
#out: {0: 0, 1: 1, 2: 2, 3: 3}
