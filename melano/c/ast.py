'''
Copied from Eli Benderski's LGPL pycparser.
'''

class AST:
	_fields = ()


class ArrayDecl(AST):
	_fields = ('type', 'dim')
	def __init__(self, type, dim):
		self.type = type
		self.dim = dim


class ArrayRef(AST):
	_fields = ('name', 'subscript')
	def __init__(self, name, subscript):
		self.name = name
		self.subscript = subscript


class Assignment(AST):
	_fields = ('lvalue', 'rvalue')
	def __init__(self, op, lvalue, rvalue):
		self.op = op
		self.lvalue = lvalue
		self.rvalue = rvalue


class BinaryOp(AST):
	_fields = ('left', 'right')
	def __init__(self, op, left, right):
		self.op = op
		self.left = left
		self.right = right


class Break(AST): pass


class Case(AST):
	_fields = ('expr', 'stmt')
	def __init__(self, expr, stmt):
		self.expr = expr
		self.stmt = stmt


class Cast(AST):
	_fields = ('to_type', 'expr')
	def __init__(self, to_type, expr):
		self.to_type = to_type
		self.expr = expr


class Compound(AST):
	_fields = ('block_items',)
	def __init__(self, *items):
		self.block_items = items


class CompoundLiteral(AST):
	_fields = ('type', 'init')
	def __init__(self, type, init):
		self.type = type
		self.init = init


class Constant(AST):
	def __init__(self, type, value):
		self.type = type
		self.value = value


class Continue(AST): pass


class Decl(AST):
	_fields = ('type', 'init', 'bitsize')
	def __init__(self, name, quals, storage, funcspec, type, init, bitsize):
		self.name = name # name: the variable being declared
		self.quals = quals # quals: list of qualifiers (const, volatile)
		self.storage = storage # storage: list of storage specifiers (extern, register, etc.)
		self.funcspec = funcspec # funcspec: list function specifiers (i.e. inline in C99)
		self.type = type # type: declaration type (probably nested with all the modifiers)
		self.init = init # init: initialization value, or None
		self.bitsize = bitsize # bitsize: bit field size, or None


class DeclList(AST):
	_fields = ('decls',)
	def __init__(self, *decls):
		self.decls = decls


class Default(AST):
	_fields = ('stmt',)
	def __init__(self, stmt):
		self.stmt = stmt


class DoWhile(AST):
	_fields = ('cond', 'stmt',)
	def __init__(self, cond, stmt):
		self.cond = cond
		self.stmt = stmt


class EllipsisParam(AST): pass


class Enum(AST):
	_fields = ('values',)
	def __init__(self, name, values):
		self.name = name # name: an optional ID
		self.values = values # values: an EnumeratorList


class Enumerator(AST):
	_fields = ('value',)
	def __init__(self, name, value):
		self.name = name # name/value pair for an enumeration value
		self.values = value


class EnumeratorList(AST):
	_fields = ('enumerators',)
	def __init__(self, *enumerators):
		self.enumerators = enumerators


class ExprList(AST):
	_fields = ('exprs',)
	def __init__(self, *exprs):
		self.exprs = exprs # a list of comma separated expressions


class For(AST):
	'''for (init; cond; next) stmt'''
	_fields = ('init', 'cond', 'next', 'stmt')
	def __init__(self, init, cond, next, stmt):
		self.init = init
		self.cond = cond
		self.next = next
		self.stmt = stmt


class FuncCall(AST):
	_fields = ('name', 'args')
	def __init__(self, name, args):
		self.name = name # Id
		self.args = args # ExprList


class FuncDecl(AST):
	'''type <decl>(args)'''
	_fields = ('args', 'type')
	def __init__(self, args, type):
		self.args = args
		self.type = type


class FuncDef(AST):
	_fields = ('decl', 'body')
	def __init__(self, decl, body):
		self.decl = decl
		self.body = body


class Goto(AST):
	def __init__(self, name):
		self.name = name


class ID(AST):
	def __init__(self, name):
		self.name = name


class IdentifierType(AST):
	def __init__(self, names):
		self.names = names


class If(AST):
	_fields = ('cond', 'iftrue', 'iffalse')
	def __init__(self, cond, iftrue, iffalse):
		self.cond = cond
		self.iftrue = iftrue
		self.iffalse = iffalse


class Label(AST):
	_fields = ('stmt',)
	def __init__(self, name, stmt):
		self.name = name
		self.stmt = stmt


class NamedInitializer(AST):
	_fields = ('attr', 'expr')
	def __init__(self, attr, expr):
		assert isinstance(attr, list)
		self.attr = attr
		self.expr = expr


class ParamList(AST):
	_fields = ('params',)
	def __init__(self, *params):
		self.params = params


class PtrDecl(AST):
	_fields = ('type',)
	def __init__(self, quals, type):
		self.quals = quals
		self.type = type


class Return(AST):
	_fields = ('expr',)
	def __init__(self, expr):
		self.expr = expr


class Struct(AST):
	_fields = ('decls',)
	def __init__(self, name, *decls):
		self.name = name
		self.decls = decls


class StructRef(AST):
	_fields = ('name', 'field')
	def __init__(self, name, type, field):
		self.name = name
		self.type = type # type: . or ->
		self.field = field


class Switch(AST):
	_fields = ('cond', 'stmt',)
	def __init__(self, cond, stmt):
		self.cond = cond
		self.stmt = stmt


class TernaryOp(AST):
	'''cond ? iftrue : iffalse'''
	_fields = ('cond', 'iftrue', 'iffalse')
	def __init__(self, cond, iftrue, iffalse):
		self.cond = cond
		self.iftrue = iftrue
		self.iffalse = iffalse


class TranslationUnit(AST):
	_fields = ('ext',)
	def __init__(self, *ext):
		self.ext = ext # declarations (Decl), Typedef or function definitions (FuncDef)


class TypeDecl(AST):
	_fields = ('type',)
	def __init__(self, declname, quals, type):
		self.declname = declname
		self.quals = quals
		self.type = type


class Typedef(AST):
	_fields = ('type',)
	def __init__(self, name, quals, storage, type):
		self.name = name
		self.quals = quals
		self.storage = storage
		self.type = type


class Typename(AST):
	_fields = ('type',)
	def __init__(self, quals, type):
		self.quals = quals
		self.type = type


class UnaryOp(AST):
	_fields = ('expr',)
	def __init__(self, op, expr):
		self.op = op
		self.expr = expr


class Union(AST):
	_fields = ('decls',)
	def __init__(self, name, *decls):
		self.name = name
		self.decls = decls


class While(AST):
	_fields = ('cond', 'stmt',)
	def __init__(self, cond, stmt):
		self.cond = cond
		self.stmt = stmt
