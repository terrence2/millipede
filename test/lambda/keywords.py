foo = lambda a, b = [], c = {}: print(a, b, c)
foo(0)
#out: 0 [] {}
foo(1, b='hello')
#out: 1 hello {}
foo('a', 'b', 'c')
#out: a b c

print(foo.__defaults__)
#out: ([], {})
print(foo.__kwdefaults__)
#out: None
