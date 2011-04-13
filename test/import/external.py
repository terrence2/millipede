import sys
print(sorted(list(set(dir(sys.modules['__main__'])) - {'__cached__'})))
#out: ['__builtins__', '__doc__', '__file__', '__name__', '__package__', 'sys']

import _tgt
print(sys.modules['_tgt'])
#out: <module '_tgt' from '/home/terrence/Projects/melano/test/import/_tgt.py'>
print(sys.modules['_tgt'].__name__)
#out: _tgt

class Foo:
	pass
import pickle

print(sorted(list(set(dir(sys.modules['__main__'])) - {'__cached__'})))
#out: ['Foo', '__builtins__', '__doc__', '__file__', '__name__', '__package__', '_tgt', 'pickle', 'sys']

rv = pickle.dumps(Foo())
print(rv)
#out: b'\x80\x03c__main__\nFoo\nq\x00)\x81q\x01}q\x02b.'

rv = pickle.dumps(_tgt.Foo())
print(rv)
#out: b'\x80\x03c_tgt\nFoo\nq\x00)\x81q\x01}q\x02b.'

import relative.relative._foo
rv = pickle.dumps(relative.relative._foo.Foo())
print(rv)
#out: b'\x80\x03crelative.relative._foo\nFoo\nq\x00)\x81q\x01}q\x02b.'

