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

