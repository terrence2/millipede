foo = 0
print(foo)
foo += 42
print(foo)
foo -= 52
print(foo)
foo *= 2
print(foo)
foo //= 10
print(foo)
foo **= 3
print(foo)
foo %= 3
print(foo)
#out: 0
#out: 42
#out: -10
#out: -20
#out: -2
#out: -8
#out: 1

b = 0.0
print(b)
b += 42
print(b)
b -= 43
print(b)
b /= 2
print(b)
b *= 4
print(b)
b **= 2
print(b)
b += 0.25
b %= 0.5
print(b)
#out: 0.0
#out: 42.0
#out: -1.0
#out: -0.5
#out: -2.0
#out: 4.0
#out: 0.25

bar = 'hello'
print(bar)
bar += ', World!'
print(bar)
#out: hello
#out: hello, World!

baz = ()
print(baz)
baz += ('foo',)
print(baz)
baz += (1,)
print(baz)
#out: ()
#out: ('foo',)
#out: ('foo', 1)

a = []
print(a)
a += [1, 'foo']
print(a)
a += [[2, 'bar']]
print(a)
#out: []
#out: [1, 'foo']
#out: [1, 'foo', [2, 'bar']]

e = set()
print(e)
e |= {'a'}
print(e)
e |= set()
print(e)
e |= {'b'}
print(e)
e &= {'b'}
print(e)
#out: set()
#out: {'a'}
#out: {'a'}
#out: {'a', 'b'}
#out: {'b'}

