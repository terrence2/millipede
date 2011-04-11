import sys
print(sorted(list(set(dir(sys.modules['__main__'])) - {'__cached__'})))
#out: ['__builtins__', '__doc__', '__file__', '__name__', '__package__', 'sys']

import _tgt
print(sys.modules['_tgt'])
#out: <module '_tgt' from '/home/terrence/Projects/melano/test/import/_tgt.py'>

class Foo:
	pass
import pickle

print(sorted(list(set(dir(sys.modules['__main__'])) - {'__cached__'})))
#out: ['Foo', '__builtins__', '__doc__', '__file__', '__name__', '__package__', '_tgt', 'pickle', 'sys']

rv = pickle.dumps(Foo())
print(b'Foo' in rv)
#out: True
