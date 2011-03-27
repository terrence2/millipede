foo = lambda * , a = 0, b = [], c = {}: print(a, b, c)
foo()
#out: 0 [] {}
foo(b='hello')
#out: 0 hello {}

print(foo.__defaults__)
#out: None
print(foo.__kwdefaults__['a'])
print(foo.__kwdefaults__['b'])
print(foo.__kwdefaults__['c'])
#out: 0
#out: []
#out: {}
