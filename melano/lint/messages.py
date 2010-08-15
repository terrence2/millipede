'''
Defines an output from the linter.
'''

class Message:
	def __init__(self, context, location=None, *args):
		self.context = context
		self.location = location
		self.extra = args

class C0111(Message):
	'''Missing docstring'''

class C0112(Message):
	'''Empty docstring'''

class C0113(Message):
	'''Missing argument annotation: '{}' '''

class C0114(Message):
	'''Missing return annotation'''

class C0201(Message):
	'''Methods should have first parameter 'self' '''

class E0201(Message):
	'''Method with no arguments'''

class C0202(Message):
	'''Class methods should have first parameter 'cls' '''

class E0202(Message):
	'''Class method with no arguments'''

class C0203(Message):
	'''Static methods should not have first parameter 'cls' or 'self' '''

class C0204(Message):
	'''Metaclass methods should have first paramter 'mcs' '''

class E0204(Message):
	'''Metaclass method with no arguments'''

class E0100(Message):
	'''__init__ method is a generator'''

class E0101(Message):
	'''Explicit return in __init__'''

class E0104(Message):
	'''Return outside function'''

class E0105(Message):
	'''Yield outside function'''

class E0106(Message):
	'''Return with argument inside generator'''

class W0401(Message):
	'''Wildcard import {}'''

class W0410(Message):
	'''__future__ import is not the first non docstring statement'''


class W0611(Message):
	'''Unused import {}'''

class W0612(Message):
	'''Unused variable {}'''

class W0613(Message):
	'''Unused argument {}'''

class W0615(Message):
	'''Unused optional variable in with statement'''

class E0601(Message):
	'''Using variable {} before assignment'''

class E0602(Message):
	'''Undefined variable {}'''

class E0603(Message):
	'''Used variable {} after unbound'''


## todo
class W0621(Message):
	'''Redefining name {} from outer scope (line {})'''

class W0622(Message):
	'''Redefining built-in {}'''

class W0631(Message):
	'''Using possibly undefined loop variable {}'''



## Need full-program linting for this
class W0614(Message):
	'''Unused import {} from wildcard import'''


#### PyFlakes Errors
#13 W0611	UnusedImport(Message):
#	W0612	UnusedAssignment
#	W0613	UnusedArgument
#27 	class ImportShadowedByLoopVar(Message):
#			NameShadowedByLoopVar
#41 	class UndefinedName(Message):
#49 	class UndefinedExport(Message):
#57 	class UndefinedLocal(Message):
#64 	class DuplicateArgument(Message):
#71 	class RedefinedFunction(Message):
#20 	class RedefinedWhileUnused(Message):
#85 	class UnusedVariable(Message):

class W0702(Message):
	'''No exception type(s) specified'''


#import time
#import f00
#def foo():
#	if time.time() % 256 == f00.bar():
#		a = time.time()
#	def bar():
#		import b4r
#		return b4r.bar(a)
#foo()()

