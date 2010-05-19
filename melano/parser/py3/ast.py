
### Base Class
class AST:
	__slots__ = ('startpos', 'endpos')
	def __init__(self, node):
		self.startpos = node.startpos
		self.endpos = node.endpos


class mod(AST):
	__slots__ = ()


class expr(AST):
	__slots__ = ()
	
	def set_context(self, ctx):
		self.ctx = ctx


class stmt(AST):
	__slots__ = ()


class keyword(AST):
	__slots__ = ('keyword', 'value')

	def __init__(self, keyword, value, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.keyword = keyword # str
		self.value = value # Name


class comprehension(AST):
	'''comprehension = (expr target, expr iter, expr* ifs)'''
	__slots__ = ('target', 'iter', 'ifs')

	def __init__(self, target, _iter, ifs, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.target = target
		self.iter = _iter
		self.ifs = ifs


class excepthandler(AST):
	__slots__ = ('test', 'target', 'suite')
	
	def __init__(self, test, target, suite, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.test = test
		self.target = target
		self.suite = suite


class arg(AST):
	__slots__ = ('arg', 'annotation')

	def __init__(self, arg, annotation, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.arg = arg
		self.annotation = annotation


#arguments = (arg* args, identifier? vararg, expr? varargannotation,
#                     arg* kwonlyargs, identifier? kwarg,
#                     expr? kwargannotation, expr* defaults,
#                     expr* kw_defaults)
class arguments(AST):
	def __init__(self,
				args, vararg, varargannotation, 
				kwonlyargs, kwarg, kwargannotation, 
				defaults, kw_defaults, *_args, **_kwargs):
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



class alias:
	def __init__(self, name, asname):
		self.name = name
		self.asname = asname


class slice(AST):
	__slots__ = ()


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


########## TOPLEVELS ############

class Module(mod):
	def __init__(self, stmts, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.stmts = stmts


########## STATEMENTS ############
#| Assert(expr test, expr? msg)
class Assert(stmt):
	def __init__(self, targets, value, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.targets = targets
		self.value = value

#| Assign(expr* targets, expr value)
class Assign(stmt):
	def __init__(self, targets, value, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.targets = targets
		self.value = value

#| AugAssign(expr target, operator op, expr value)
class AugAssign(stmt):
	def __init__(self, target, op, value, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.target = target
		self.op = op
		self.value = value

#| Break
class Break(stmt): pass

#| ClassDef(identifier name, expr* bases, keyword* keywords, expr? starargs, expr? kwargs, stmt* body, expr *decorator_list)
class ClassDef(stmt):
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
class Continue(stmt): pass

#| Delete(expr* targets)
class Delete(stmt):
	def __init__(self, targets, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.targets = targets	

#| Expr(expr value)
class Expr(stmt):
	def __init__(self, value, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.value = value

#| For(expr target, expr iter, stmt* body, stmt* orelse)
class For(stmt):
	def __init__(self, target, _iter, body, orelse, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.target = target
		self.iter = _iter
		self.body = body
		self.orelse = orelse

#| Global(identifier* names)
class Global(stmt):
	def __init__(self, names, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.names = names

#| If(expr test, stmt* body, stmt* orelse)
class If(stmt):
	def __init__(self, test, body, orelse, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.test = test
		self.body = body
		self.orelse = orelse

#| Import(alias* names)
class Import(stmt):
	def __init__(self, names, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.names = names

#| ImportFrom(identifier module, alias* names, int? level)
class ImportFrom(stmt):
	def __init__(self, module, names, level, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.module = module
		self.names = names
		self.level = level

#| Nonlocal(identifier* names)
class Nonlocal(stmt):
	def __init__(self, names, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.names = names

#| Pass
class Pass(stmt): pass

#| Raise(expr? exc, expr? cause)
class Raise(stmt):
	def __init__(self, exc, cause, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.exc = exc
		self.cause = cause

#| Return(expr? value)
class Return(stmt):
	def __init__(self, value, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.value = value

#| TryExcept(stmt* body, excepthandler* handlers, stmt* orelse)
class TryExcept(stmt):
	def __init__(self, body, handlers, orelse, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.body = body
		self.handlers = handlers
		self.orelse = orelse

#| TryFinally(stmt* body, stmt* finalbody)
class TryFinally(stmt):
	def __init__(self, body, finalbody, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.body = body
		self.finalbody = finalbody

#| While(expr test, stmt* body, stmt* orelse)
class While(stmt):
	def __init__(self, test, body, orelse, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.test = test
		self.body = body
		self.orelse = orelse

#| With(expr context_expr, expr? optional_vars, stmt* body)
class With(stmt):
	def __init__(self, context_expr, optional_vars, body, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.context_expr = context_expr
		self.optional_vars = optional_vars
		self.body = body

#| FunctionDef(identifier name, arguments args, stmt* body, expr* decorator_list, expr? returns)
class FunctionDef(stmt):
	def __init__(self, name, _args, body, decorator_list, _returns, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.name = name
		self.args = _args # an ast.arguments
		self.body = body
		self.decorator_list = decorator_list
		self.returns = _returns



########## EXPRESSIONS ############

#| Attribute(expr value, identifier attr, expr_context ctx)
class Attribute(expr):
	def __init__(self, value, attr, ctx, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.value = value
		self.attr = attr
		self.ctx = ctx

#| BinOp(expr left, operator op, expr right)
class BinOp(expr):
	def __init__(self, left, op, right, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.left = left
		self.op = op
		self.right = right

#| BoolOp(boolop op, expr* values)
class BoolOp(expr):
	def __init__(self, op, values, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.op = op
		self.values = values

#| Bytes(string s)
class Bytes(expr):
	def __init__(self, s, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.s = s

#| Call(expr func, expr* args, keyword* keywords, expr? starargs, expr? kwargs)
class Call(expr):
	def __init__(self, func, _args, _keywords, starargs, _kwargs, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.func = func
		self.args = _args
		self.keywords = _keywords
		self.starargs = starargs
		self.kwargs = _kwargs

#| Compare(expr left, cmpop* ops, expr* comparators)
class Compare(expr):
	def __init__(self, left, ops, comparators, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.left = left
		self.ops = ops
		self.comparators = comparators

#| Dict(expr* keys, expr* values)
class Dict(expr):
	def __init__(self, keys, values, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.keys = keys
		self.values = values

#| DictComp(expr key, expr value, comprehension* generators)
class DictComp(expr):
	def __init__(self, key, value, generators, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.key = key
		self.value = value
		self.generators = generators

#| Ellipsis
class Ellipsis(expr): pass

#| GeneratorExp(expr elt, comprehension* generators)
class GeneratorExp(expr):
	def __init__(self, elt, generators, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.elt = elt
		self.generators = generators

#| IfExp(expr test, expr body, expr orelse)
class IfExp(expr):
	def __init__(self, test, body, orelse, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.test = test
		self.body = body
		self.orelse = orelse

#| Lambda(arguments args, expr body)
class Lambda(expr):
	def __init__(self, _args, body, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.args = _args
		self.body = body

#| List(expr* elts, expr_context ctx) 
class List(expr):
	def __init__(self, elts, ctx, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.elts = elts
		self.ctx = ctx

#| ListComp(expr elt, comprehension* generators)
class ListComp(expr):
	def __init__(self, elt, generators, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.elt = elt
		self.generators = generators

#| Name(identifier id, expr_context ctx)
class Name(expr):
	def __init__(self, _id, ctx, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.id = _id
		self.ctx = ctx

#| Num(object n) -- a number as a PyObject.
class Num(expr):
	def __init__(self, n, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.n = n

#| Set(expr* elts)
class Set(expr):
	def __init__(self, elts, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.elts = elts

#| SetComp(expr elt, comprehension* generators)
class SetComp(expr):
	def __init__(self, elt, generators, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.elt = elt
		self.generators = generators

#| Starred(expr value, expr_context ctx)
class Starred(expr):
	def __init__(self, value, ctx, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.value = value
		self.ctx = ctx

#| Str(string s) -- need to specify raw, unicode, etc?
class Str(expr):
	def __init__(self, s, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.s = s

#| Subscript(expr value, slice slice, expr_context ctx)
class Subscript(expr):
	def __init__(self, value, _slice, ctx, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.value = value
		self.slice = _slice
		self.ctx = ctx

#| Tuple(expr* elts, expr_context ctx)
class Tuple(expr):
	def __init__(self, elts, ctx, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.elts = elts
		self.ctx = ctx

#| UnaryOp(unaryop op, expr operand)
class UnaryOp(expr):
	def __init__(self, op, operand, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.op = op
		self.operand = operand

#| Yield(expr? value)
class Yield(expr):
	def __init__(self, value, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.value = value



### Terminals

class Slice(slice):
	__slots__ = ('lower', 'upper', 'step')
	def __init__(self, lower:expr, upper:expr, step:expr, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.lower = lower
		self.upper = upper
		self.step = step


class ExtSlice(slice):
	__slots__ = ('dims')
	def __init__(self, dims:slice, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.dims = dims


class Index(slice):
	__slots__ = ('value')
	def __init__(self, value:expr, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.value = value


