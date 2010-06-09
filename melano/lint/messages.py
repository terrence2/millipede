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

