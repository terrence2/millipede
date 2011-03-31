import relative
print(type(relative._foo))
#out: <class 'function'>

import relative._foo
print(type(relative._foo))
#out: <class 'module'>
