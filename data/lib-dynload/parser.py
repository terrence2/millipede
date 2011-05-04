class ParserError(Exception): pass

class st:
	'''Intermediate representation of a Python parse tree.'''
	def compile(self, *args, **kwargs): pass
	def isexpr(self, *args, **kwargs): pass
	def issuite(self, *args, **kwargs): pass
	def tolist(self, *args, **kwargs): pass
	def totuple(self, *args, **kwargs): pass


STType = st
def compilest(*args, **kwargs): pass
def expr(*args, **kwargs): pass
def isexpr(*args, **kwargs): pass
def issuite(*args, **kwargs): pass
def sequence2st(*args, **kwargs): pass
def st2list(*args, **kwargs): pass
def st2tuple(*args, **kwargs): pass
def suite(*args, **kwargs): pass
def tuple2st(*args, **kwargs): pass
