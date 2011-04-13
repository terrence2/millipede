class Foo: pass

print(Foo.__name__)
#out: Foo
print(Foo.__module__)
#out: __main__
print(Foo().__module__)
#out: __main__
