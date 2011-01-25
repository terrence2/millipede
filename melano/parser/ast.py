'''
Copyright (c) 2011-2011, Terrence Cole.
All rights reserved.

All AST nodes.  Built manually from inspection of:
   http://docs.python.org/py3k/library/ast.html
'''

### Context Types
Load = 0
Store = 1
Del = 2
AugLoad = 3
AugStore = 4
Param = 5
Aug = 6


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


class AST:
	'''Base class of all ast nodes.'''

	__slots__ = ('symbol', 'hl', 'start', 'end') #'llnode')
	def __init__(self, llnode):
		#self.llnode = None
		self.hl = None
		self.symbol = None
		self.start = llnode.startpos
		self.end = llnode.endpos

	def llcopy(self, other):
		'''Take low-level parameters from the other node.'''
		#self.llnode = other.llnode
		self.start = other.start
		self.end = other.end

	def __repr__(self):
		return '<' + self.__class__.__name__ + '>'

	#@property
	#def start(self):
	#	return self.llnode.startpos

	#@property
	#def end(self):
	#	return self.llnode.endpos


### Base Class
class mod(AST):
	__slots__ = ()


class expr(AST):
	__slots__ = ()

	def set_context(self, ctx):
		self.ctx = ctx


class stmt(AST):
	__slots__ = ()


#| keyword = (identifier arg, expr value)
class keyword(AST):
	_fields = ('value',)
	__slots__ = ('keyword', 'value')
	def __init__(self, keyword:str, value:expr, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.keyword = keyword # str
		self.value = value # Name


#| comprehension = (expr target, expr iter, expr* ifs)
class comprehension(AST):
	_fields = ('target', 'iter', 'ifs')
	__slots__ = ('target', 'iter', 'ifs')
	def __init__(self, target:expr, _iter:expr, ifs:[expr], *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.target = target
		self.iter = _iter
		self.ifs = ifs


#| excepthandler = ExceptHandler(expr? type, identifier? name, stmt* body)
class excepthandler(AST):
	_fields = ('type', 'body')
	__slots__ = ('type', 'name', 'body')
	def __init__(self, type_:expr, name:str, body:[stmt], *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.type = type_
		self.name = name
		self.body = body


#| arg = (identifier arg, expr? annotation)
class arg(AST):
	_fields = ('annotation',)
	__slots__ = ('arg', 'annotation')
	def __init__(self, arg, annotation:expr, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.arg = arg # Name
		self.annotation = annotation


#arguments = (arg* args, identifier? vararg, expr? varargannotation,
#                     arg* kwonlyargs, identifier? kwarg,
#                     expr? kwargannotation, expr* defaults,
#                     expr* kw_defaults)
class arguments(AST):
	_fields = ('args', 'varargannotation',
				'kwonlyargs', 'kwargannotation',
				'defaults', 'kw_defaults')
	__slots__ = ('args', 'vararg', 'varargannotation',
				'kwonlyargs', 'kwarg', 'kwargannotation',
				'defaults', 'kw_defaults')
	def __init__(self,
				args:[arg], vararg:str, varargannotation:expr,
				kwonlyargs:[arg], kwarg:str, kwargannotation:expr,
				defaults:[expr], kw_defaults:[expr], *_args, **_kwargs):
		super().__init__(*_args, **_kwargs)
		self.args = args # list: all arg up to *args, in order, as ast.arg
		self.defaults = defaults # list of all provided default arguments for 
						# args in .args; index against args, starting from the 
						# end of both lists, since this can be shorter.

		self.vararg = vararg # str: name of the *arg or None if none passed
		self.varargannotation = varargannotation # an annotation on the *arg or None

		self.kwonlyargs = kwonlyargs # list: all args after *args as ast.arg
		self.kw_defaults = kw_defaults # list: defaults for kwonlyargs.  Unlike
						# with .defaults, this has None for any slots in kwonlyargs
						# that do not provide a default argument.

		self.kwarg = kwarg # str: name of **kwarg or None if none passed
		self.kwargannotation = kwargannotation # an annotation on the **arg or None


#| alias = (identifier name, identifier? asname)
class alias:
	__slots__ = ('name', 'asname')
	def __init__(self, name:object, asname:str):
		self.name = name
		self.asname = asname


class slice_(AST):
	__slots__ = ()




########## TOPLEVELS ############

#| Module(stmt* body)
class Module(mod):
	_fields = ('body',)
	__slots__ = ('body',)
	def __init__(self, body:[stmt], *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.body = body


########## STATEMENTS ############
#| Assert(expr test, expr? msg)
class Assert(stmt):
	_fields = ('test', 'msg')
	__slots__ = ('test', 'msg')
	def __init__(self, test, msg, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.test = test
		self.msg = msg

#| Assign(expr* targets, expr value)
class Assign(stmt):
	_fields = ('targets', 'value')
	__slots__ = ('targets', 'value')
	def __init__(self, targets, value, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.targets = targets
		self.value = value

#| AugAssign(expr target, operator op, expr value)
class AugAssign(stmt):
	_fields = ('target', 'value')
	__slots__ = ('target', 'op', 'value')
	def __init__(self, target, op, value, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.target = target
		self.op = op
		self.value = value

#| Break
class Break(stmt):
	_fields = ()
	__slots__ = ()

#| ClassDef(identifier name, expr* bases, keyword* keywords, expr? starargs, expr? kwargs, stmt* body, expr *decorator_list)
class ClassDef(stmt):
	_fields = ('bases', 'keywords', 'starargs', 'kwargs', 'body', 'decorator_list')
	__slots__ = ('name', 'bases', 'keywords', 'starargs', 'kwargs', 'body', 'decorator_list')
	def __init__(self, name, bases, keywords, starargs, _kwargs, body, decorator_list, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.name = name
		self.bases = bases
		self.keywords = keywords
		self.starargs = starargs
		self.kwargs = _kwargs
		self.body = body
		self.decorator_list = decorator_list

#| Continue
class Continue(stmt):
	_fields = ()
	__slots__ = ()

#| Delete(expr* targets)
class Delete(stmt):
	_fields = ('targets',)
	__slots__ = ('targets',)
	def __init__(self, targets, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.targets = targets

#| Expr(expr value)
class Expr(stmt):
	_fields = ('value',)
	__slots__ = ('value',)
	def __init__(self, value, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.value = value

#| For(expr target, expr iter, stmt* body, stmt* orelse)
class For(stmt):
	_fields = ('target', 'iter', 'body', 'orelse')
	__slots__ = ('target', 'iter', 'body', 'orelse')
	def __init__(self, target, _iter, body, orelse, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.target = target
		self.iter = _iter
		self.body = body
		self.orelse = orelse

#| Global(identifier* names)
class Global(stmt):
	_fields = ('names',)
	__slots__ = ('names',)
	def __init__(self, names, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.names = names

#| If(expr test, stmt* body, stmt* orelse)
class If(stmt):
	_fields = ('test', 'body', 'orelse')
	__slots__ = ('test', 'body', 'orelse')
	def __init__(self, test, body, orelse, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.test = test
		self.body = body
		self.orelse = orelse

#| Import(alias* names)
class Import(stmt):
	_fields = ('names',)
	__slots__ = ('names',)
	def __init__(self, names, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.names = names

#| ImportFrom(identifier module, alias* names, int? level)
class ImportFrom(stmt):
	_fields = ()
	__slots__ = ('module', 'names', 'level')
	def __init__(self, module, names, level, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.module = module
		self.names = names
		self.level = level

#| Nonlocal(identifier* names)
class Nonlocal(stmt):
	_fields = ('names',)
	__slots__ = ('names',)
	def __init__(self, names, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.names = names

#| Pass
class Pass(stmt):
	_fields = ()
	__slots__ = ()

#| Raise(expr? exc, expr? cause)
class Raise(stmt):
	_fields = ('exc', 'cause')
	__slots__ = ('exc', 'cause')
	def __init__(self, exc, cause, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.exc = exc
		self.cause = cause

#| Return(expr? value)
class Return(stmt):
	_fields = ('value',)
	__slots__ = ('value',)
	def __init__(self, value, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.value = value

#| TryExcept(stmt* body, excepthandler* handlers, stmt* orelse)
class TryExcept(stmt):
	_fields = ('body', 'handlers', 'orelse')
	__slots__ = ('body', 'handlers', 'orelse')
	def __init__(self, body, handlers, orelse, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.body = body
		self.handlers = handlers
		self.orelse = orelse

#| TryFinally(stmt* body, stmt* finalbody)
class TryFinally(stmt):
	_fields = ('body', 'finalbody')
	__slots__ = ('body', 'finalbody')
	def __init__(self, body, finalbody, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.body = body
		self.finalbody = finalbody

#| While(expr test, stmt* body, stmt* orelse)
class While(stmt):
	_fields = ('test', 'body', 'orelse')
	__slots__ = ('test', 'body', 'orelse')
	def __init__(self, test, body, orelse, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.test = test
		self.body = body
		self.orelse = orelse

#| With(expr context_expr, expr? optional_vars, stmt* body)
class With(stmt):
	_fields = ('context_expr', 'optional_vars', 'body')
	__slots__ = ('context_expr', 'optional_vars', 'body')
	def __init__(self, context_expr, optional_vars, body, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.context_expr = context_expr
		self.optional_vars = optional_vars
		self.body = body

#| FunctionDef(identifier name, arguments args, stmt* body, expr* decorator_list, expr? returns)
class FunctionDef(stmt):
	_fields = ('args', 'body', 'decorator_list', 'returns')
	__slots__ = ('name', 'args', 'body', 'decorator_list', 'returns')
	def __init__(self, name, _args, body, decorator_list, _returns, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.name = name
		self.args = _args
		self.body = body
		self.decorator_list = decorator_list
		self.returns = _returns



########## EXPRESSIONS ############

#| Attribute(expr value, identifier attr, expr_context ctx)
class Attribute(expr):
	_fields = ('value',)
	__slots__ = ('value', 'attr', 'ctx')
	def __init__(self, value, attr, ctx, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.value = value
		self.attr = attr
		self.ctx = ctx

	def first(self):
		'Returns the Name from the left most entry in the dotted list.'
		if not isinstance(self.value, Attribute):
			return self.value
		return self.value.first()

	def __str__(self):
		return str(self.value) + '.' + str(self.attr)


#| BinOp(expr left, operator op, expr right)
class BinOp(expr):
	_fields = ('left', 'right')
	__slots__ = ('left', 'op', 'right')
	def __init__(self, left, op, right, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.left = left
		self.op = op
		self.right = right

#| BoolOp(boolop op, expr* values)
class BoolOp(expr):
	_fields = ('values',)
	__slots__ = ('op', 'values')
	def __init__(self, op, values, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.op = op
		self.values = values

#| Bytes(string s)
class Bytes(expr):
	_fields = ()
	__slots__ = ('s',)
	def __init__(self, s, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.s = s

#| Call(expr func, expr* args, keyword* keywords, expr? starargs, expr? kwargs)
class Call(expr):
	_fields = ('func', 'args', 'keywords', 'starargs', 'kwargs')
	__slots__ = ('func', 'args', 'keywords', 'starargs', 'kwargs')
	def __init__(self, func, _args, _keywords, starargs, _kwargs, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.func = func
		self.args = _args
		self.keywords = _keywords
		self.starargs = starargs
		self.kwargs = _kwargs

#| Compare(expr left, cmpop* ops, expr* comparators)
class Compare(expr):
	_fields = ('left', 'ops', 'comparators')
	__slots__ = ('left', 'ops', 'comparators')
	def __init__(self, left, ops, comparators, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.left = left
		self.ops = ops
		self.comparators = comparators

#| Dict(expr* keys, expr* values)
class Dict(expr):
	_fields = ('keys', 'values',)
	__slots__ = ('keys', 'values')
	def __init__(self, keys, values, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.keys = keys
		self.values = values

#| DictComp(expr key, expr value, comprehension* generators)
class DictComp(expr):
	_fields = ('key', 'value', 'generators')
	__slots__ = ('key', 'value', 'generators')
	def __init__(self, key, value, generators, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.key = key
		self.value = value
		self.generators = generators

#| Ellipsis
class Ellipsis(expr):
	_fields = ()
	__slots__ = ()

#| GeneratorExp(expr elt, comprehension* generators)
class GeneratorExp(expr):
	_fields = ('elt', 'generators')
	__slots__ = ('elt', 'generators')
	def __init__(self, elt, generators, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.elt = elt
		self.generators = generators

#| IfExp(expr test, expr body, expr orelse)
class IfExp(expr):
	_fields = ('test', 'body', 'orelse')
	__slots__ = ('test', 'body', 'orelse')
	def __init__(self, test, body, orelse, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.test = test
		self.body = body
		self.orelse = orelse

#| Lambda(arguments args, expr body)
class Lambda(expr):
	_fields = ('args', 'body')
	__slots__ = ('args', 'body')
	def __init__(self, _args, body, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.args = _args
		self.body = body

#| List(expr* elts, expr_context ctx) 
class List(expr):
	_fields = ('elts',)
	__slots__ = ('elts', 'ctx')
	def __init__(self, elts, ctx, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.elts = elts
		self.ctx = ctx

#| ListComp(expr elt, comprehension* generators)
class ListComp(expr):
	_fields = ('elt', 'generators')
	__slots__ = ('elt', 'generators')
	def __init__(self, elt, generators, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.elt = elt
		self.generators = generators

#| Name(identifier id, expr_context ctx)
class Name(expr):
	_fields = ()
	__slots__ = ('id', 'ctx')
	def __init__(self, _id, ctx, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.id = _id
		self.ctx = ctx

	def __str__(self):
		return self.id

#| Num(object n) -- a number as a PyObject.
class Num(expr):
	_fields = ()
	__slots__ = ('n',)
	def __init__(self, n, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.n = n

#| Set(expr* elts)
class Set(expr):
	_fields = ('elts',)
	__slots__ = ('elts',)
	def __init__(self, elts, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.elts = elts

#| SetComp(expr elt, comprehension* generators)
class SetComp(expr):
	_fields = ('elt', 'generators')
	__slots__ = ('elt', 'generators')
	def __init__(self, elt, generators, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.elt = elt
		self.generators = generators

#| Starred(expr value, expr_context ctx)
class Starred(expr):
	_fields = ('value',)
	__slots__ = ('value', 'ctx')
	def __init__(self, value, ctx, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.value = value
		self.ctx = ctx

#| Str(string s) -- need to specify raw, unicode, etc?
class Str(expr):
	_fields = ()
	__slots__ = ('s',)
	def __init__(self, s, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.s = s

#| Subscript(expr value, slice slice, expr_context ctx)
class Subscript(expr):
	_fields = ('value',)
	__slots__ = ('value', 'slice', 'ctx')
	def __init__(self, value, _slice, ctx, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.value = value
		self.slice = _slice
		self.ctx = ctx

#| Tuple(expr* elts, expr_context ctx)
class Tuple(expr):
	_fields = ('elts',)
	__slots__ = ('elts', 'ctx')
	def __init__(self, elts, ctx, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.elts = elts
		self.ctx = ctx

#| UnaryOp(unaryop op, expr operand)
class UnaryOp(expr):
	_fields = ('operand',)
	__slots__ = ('op', 'operand')
	def __init__(self, op, operand, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.op = op
		self.operand = operand

#| Yield(expr? value)
class Yield(expr):
	_fields = ('value',)
	__slots__ = ('value',)
	def __init__(self, value, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.value = value



### Terminals

#| Slice(expr? lower, expr? upper, expr? step) 
class Slice(slice_):
	__slots__ = ('lower', 'upper', 'step')
	def __init__(self, lower:expr, upper:expr, step:expr, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.lower = lower
		self.upper = upper
		self.step = step

#| ExtSlice(slice* dims) 
class ExtSlice(slice_):
	_fields = ('dims',)
	__slots__ = ('dims',)
	def __init__(self, dims:slice, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.dims = dims

#| Index(expr value)
class Index(slice_):
	_fields = ('value',)
	__slots__ = ('value',)
	def __init__(self, value:expr, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.value = value


