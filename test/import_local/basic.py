#import sys
#sys.path = ['test/import_local'] + sys.path
from _tgt import foo
foo()
#out: foo

#FIXME: is there a way for us to tell if this was internal or from another file?
