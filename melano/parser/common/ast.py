

class AST:
	'''Base class of all ast nodes.'''

	__slots__ = ('startpos', 'endpos')
	def __init__(self, node):
		self.startpos = node.startpos
		self.endpos = node.endpos


### Context Types
Load = 0
Store = 1
Del = 2
AugLoad = 3
AugStore = 4
Param = 5


### BinOperator Types
BitOr = 0
BitXor = 1
BitAnd = 2
LShift = 3
RShift = 4
Add = 5
Sub = 6
Mult = 7
Div = 8
FloorDiv = 9
Mod = 10
Pow = 11


### Unary Operator Types
Invert = 0
Not = 1
UAdd = 2
USub = 3


### Comparison Types
Eq = 0
NotEq = 1
Lt = 2
LtE = 3
Gt = 4
GtE = 5
Is = 6
IsNot = 7
In = 8
NotIn = 9


### Bool Ops
And = 0
Or = 1

