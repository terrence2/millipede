def mylen(a):
	return 42

import builtins
builtins.mylen = mylen
builtins.len = mylen
