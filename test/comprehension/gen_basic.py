a = 'hello'
b = (a for a in range(4))
print(a)
print(type(b))
print(list(b))
print(list(b))
#out: hello
#out: <class 'generator'>
#out: [0, 1, 2, 3]
#out: []
