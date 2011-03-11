class A: pass
a = A()
a.b = A()
a.b.c = A()
a.b.c.d = A()
print(a.__class__.__name__)
print(a.b.__class__.__name__)
print(a.b.c.__class__.__name__)
print(a.b.c.d.__class__.__name__)

#out: A
#out: A
#out: A
#out: A
