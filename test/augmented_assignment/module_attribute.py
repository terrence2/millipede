class A: pass
a = A()
a.b = A()
a.b.c = A()

a.b.c.foo = 0
print(a.b.c.foo)
a.b.c.foo += 42
print(a.b.c.foo)
a.b.c.foo -= 52
print(a.b.c.foo)
a.b.c.foo *= 2
print(a.b.c.foo)
a.b.c.foo //= 10
print(a.b.c.foo)
a.b.c.foo **= 3
print(a.b.c.foo)
a.b.c.foo %= 3
print(a.b.c.foo)
#out: 0
#out: 42
#out: -10
#out: -20
#out: -2
#out: -8
#out: 1

a.b.c.b = 0.0
print(a.b.c.b)
a.b.c.b += 42
print(a.b.c.b)
a.b.c.b -= 43
print(a.b.c.b)
a.b.c.b /= 2
print(a.b.c.b)
a.b.c.b *= 4
print(a.b.c.b)
a.b.c.b **= 2
print(a.b.c.b)
a.b.c.b += 0.25
a.b.c.b %= 0.5
print(a.b.c.b)
#out: 0.0
#out: 42.0
#out: -1.0
#out: -0.5
#out: -2.0
#out: 4.0
#out: 0.25

a.b.c.bar = 'hello'
print(a.b.c.bar)
a.b.c.bar += ', World!'
print(a.b.c.bar)
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

a.b.c.a = []
print(a.b.c.a)
a.b.c.a += [1, 'foo']
print(a.b.c.a)
a.b.c.a += [[2, 'bar']]
print(a.b.c.a)
#out: []
#out: [1, 'foo']
#out: [1, 'foo', [2, 'bar']]

a.b.c.e = set()
print(a.b.c.e)
a.b.c.e |= {'a'}
print(a.b.c.e)
a.b.c.e |= set()
print(a.b.c.e)
a.b.c.e |= {'b'}
print(a.b.c.e)
a.b.c.e &= {'b'}
print(a.b.c.e)
#out: set()
#out: {'a'}
#out: {'a'}
#out: {'a', 'b'}
#out: {'b'}

