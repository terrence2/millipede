'''
Copied from Eli Benderski's LGPL pycparser.
'''
from melano.c.keywords import C_KEYWORDS
from melano.lang.ast import AST
import itertools

class CPP(AST):
	'''type for preprocessor nodes'''


class ArrayDecl(AST):
	_fields = ('type', 'dim')
	def __init__(self, type, dim):
		super().__init__(None)
		self.type = type
		self.dim = dim


class ArrayRef(AST):
	_fields = ('name', 'subscript')
	def __init__(self, name, subscript):
		super().__init__(None)
		self.name = name
		self.subscript = subscript


class Assignment(AST):
	_fields = ('lvalue', 'rvalue')
	def __init__(self, op, lvalue, rvalue):
		super().__init__(None)
		self.op = op
		self.lvalue = lvalue
		self.rvalue = rvalue


class BinaryOp(AST):
	_fields = ('left', 'right')
	def __init__(self, op, left, right):
		super().__init__(None)
		self.op = op
		self.left = left
		self.right = right


class Break(AST):
	def __init__(self):
		super().__init__(None)


class Case(AST):
	_fields = ('expr', 'stmt')
	def __init__(self, expr, stmt):
		super().__init__(None)
		self.expr = expr
		self.stmt = stmt


class Cast(AST):
	_fields = ('to_type', 'expr')
	def __init__(self, to_type, expr):
		super().__init__(None)
		self.to_type = to_type
		self.expr = expr


class Comment(AST):
	def __init__(self, value):
		super().__init__(None)
		self.value = value


class Compound(AST):
	_fields = ('block_items',)
	def __init__(self, *items):
		super().__init__(None)

		self.block_items = list(items)

		# we insert variables at the front of the function
		self._vars_pos = 0

		# track which variables need a call to cleanup at compound out
		self.cleanup = []
		# map from ll variable names to hl symbols (and existence markers)
		self.names = set()
		# counter for tmp items
		self.tmpcount = itertools.count()


	def tmpname(self, tu):
		return self.reserve_name('tmp' + str(next(self.tmpcount)), tu)


	def reserve_name(self, name, tu):
		'''
		Try to ensure uniqueness in the local scope and against the global scope.  We _should_ only
		ever care about names in the global scope that we use in the local scope, so if someone
		introduces a name into the global scope later that aliases with something we've already
		added to the local scope, then it shouldn't matter because we don't have interest in that 
		global name, only the local one we are aliasing.  This, of course, breaks down if we happen
		to alias with one of our internal names, which is why we have this particular indirection.
		'''
		cnt = 0
		nm = name
		while nm in self.names or (tu and nm in tu.names) or nm in C_KEYWORDS:
			nm = name + '_' + str(cnt)
			cnt += 1
		self.names.add(nm)
		tu.mask.add(nm)
		return nm

	def has_name(self, name):
		return name in self.names

	def has_symbol(self, sym):
		return sym in set(self.names.values())

	def add_variable(self, decl, need_cleanup=True):
		self.block_items.insert(self._vars_pos, decl)
		self._vars_pos += 1
		if need_cleanup:
			self.cleanup.append(decl.name)

	def add(self, node):
		self.block_items.append(node)
		return node


class CompoundLiteral(AST):
	_fields = ('type', 'init')
	def __init__(self, type, init):
		super().__init__(None)
		self.type = type
		self.init = init


class Constant(AST):
	def __init__(self, type, value, prefix='', postfix=''):
		super().__init__(None)
		self.type = type
		self.value = value
		self.prefix = prefix
		self.postfix = postfix


class Continue(AST): pass


class Decl(AST):
	_fields = ('type', 'init', 'bitsize')
	def __init__(self, name, type, quals=[], storage=[], funcspec=[], init=None, bitsize=None):
		super().__init__(None)
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
		super().__init__(None)
		self.decls = decls


class Default(AST):
	_fields = ('stmt',)
	def __init__(self, stmt):
		super().__init__(None)
		self.stmt = stmt


class DoWhile(AST):
	_fields = ('cond', 'stmt',)
	def __init__(self, cond, stmt):
		super().__init__(None)
		self.cond = cond
		self.stmt = stmt


class EllipsisParam(AST): pass


class Enum(AST):
	_fields = ('values',)
	def __init__(self, name, values):
		super().__init__(None)
		self.name = name # name: an optional ID
		self.values = values # values: an EnumeratorList


class Enumerator(AST):
	_fields = ('value',)
	def __init__(self, name, value):
		super().__init__(None)
		self.name = name # name/value pair for an enumeration value
		self.values = value


class EnumeratorList(AST):
	_fields = ('enumerators',)
	def __init__(self, *enumerators):
		super().__init__(None)
		self.enumerators = enumerators


class ExprList(AST):
	_fields = ('exprs',)
	def __init__(self, *exprs):
		super().__init__(None)
		self.exprs = exprs # a list of comma separated expressions


class For(AST):
	'''for (init; cond; next) stmt'''
	_fields = ('init', 'cond', 'next', 'stmt')
	def __init__(self, init, cond, next, stmt):
		super().__init__(None)
		self.init = init
		self.cond = cond
		self.next = next
		self.stmt = stmt


class FuncCall(AST):
	_fields = ('name', 'args')
	def __init__(self, name, args):
		super().__init__(None)
		self.name = name # Id
		self.args = args # ExprList


class FuncDecl(AST):
	'''type <decl>(args)'''
	_fields = ('args', 'type')
	def __init__(self, args, type):
		super().__init__(None)
		self.args = args
		self.type = type


class FuncDef(AST):
	_fields = ('decl', 'body')
	def __init__(self, decl, body):
		super().__init__(None)
		assert isinstance(body, Compound), "Techically the body could be any stmt... but it's going to be a compound anyway."
		self.decl = decl
		self.body = body


class Goto(AST):
	def __init__(self, name):
		super().__init__(None)
		self.name = name


class ID(AST):
	def __init__(self, name):
		super().__init__(None)
		assert isinstance(name, str)
		self.name = name


class IdentifierType(AST):
	def __init__(self, *names):
		super().__init__(None)
		self.names = names


class If(AST):
	_fields = ('cond', 'iftrue', 'iffalse')
	def __init__(self, cond, iftrue, iffalse):
		super().__init__(None)
		self.cond = cond
		self.iftrue = iftrue
		self.iffalse = iffalse


class Include(CPP):
	def __init__(self, name, is_system=False):
		super().__init__(None)
		self.name = name
		self.is_system = is_system


class Label(AST):
	_fields = ('stmt',)
	def __init__(self, name, stmt=None):
		super().__init__(None)
		self.name = name
		self.stmt = stmt


class NamedInitializer(AST):
	_fields = ('attr', 'expr')
	def __init__(self, attr, expr):
		super().__init__(None)
		assert isinstance(attr, list)
		self.attr = attr
		self.expr = expr


class ParamList(AST):
	_fields = ('params',)
	def __init__(self, *params):
		super().__init__(None)
		self.params = list(params)


class PtrDecl(AST):
	_fields = ('type',)
	def __init__(self, type, quals=[]):
		super().__init__(None)
		self.quals = quals
		self.type = type


class Return(AST):
	_fields = ('expr',)
	def __init__(self, expr):
		super().__init__(None)
		self.expr = expr


class Struct(AST):
	_fields = ('decls',)
	def __init__(self, name, *decls):
		super().__init__(None)
		self.name = name
		self.decls = list(decls)


class StructRef(AST):
	_fields = ('name', 'field')
	def __init__(self, name, type, field):
		super().__init__(None)
		self.name = name
		self.type = type # type: . or ->
		self.field = field


class Switch(AST):
	_fields = ('cond', 'stmt',)
	def __init__(self, cond, stmt):
		super().__init__(None)
		self.cond = cond
		self.stmt = stmt


class TernaryOp(AST):
	'''cond ? iftrue : iffalse'''
	_fields = ('cond', 'iftrue', 'iffalse')
	def __init__(self, cond, iftrue, iffalse):
		super().__init__(None)
		self.cond = cond
		self.iftrue = iftrue
		self.iffalse = iffalse


class TranslationUnit(AST):
	_fields = ('ext',)
	def __init__(self, *ext):
		super().__init__(None)
		self.ext = list(ext) # declarations (Decl), Typedef or function definitions (FuncDef)
		self._inc_pos = 0
		self._var_pos = 0
		self._fwddecl_pos = 0
		# map from ll variable names to hl symbols (and existence markers)
		self.names = set()
		# mask names defined at a higher level so that we don't override something defined earlier in a different scope
		self.mask = set()

		# note: need to allow declare to check ourself as well
		self.tu = self

	def reserve_global_name(self, name):
		cnt = 0
		if name.startswith('__'):
			nm = '__mp_' + name[2:]
		else:
			nm = 'mp_' + name
		while nm in self.names or nm in self.mask or nm in C_KEYWORDS:
			nm = name + '_' + str(cnt)
			cnt += 1
		self.names.add(nm)
		return nm

	def add_include(self, inc):
		self.ext.insert(self._inc_pos, inc)
		self._inc_pos += 1
		self._var_pos += 1
		self._fwddecl_pos += 1

	def add_variable(self, decl, need_cleanup=None):
		self.ext.insert(self._var_pos, decl)
		self._var_pos += 1
		self._fwddecl_pos += 1

	def add_fwddecl(self, decl):
		self.ext.insert(self._fwddecl_pos, decl)
		self._fwddecl_pos += 1

	def add(self, node):
		self.ext.append(node)
		return node


class TypeDecl(AST):
	_fields = ('type',)
	def __init__(self, declname, type, quals=[]):
		super().__init__(None)
		self.declname = declname
		self.quals = quals
		self.type = type


class Typedef(AST):
	_fields = ('type',)
	def __init__(self, name, quals, storage, type):
		super().__init__(None)
		self.name = name
		self.quals = quals
		self.storage = storage
		self.type = type


class Typename(AST):
	_fields = ('type',)
	def __init__(self, quals, type):
		super().__init__(None)
		self.quals = quals
		self.type = type


class UnaryOp(AST):
	_fields = ('expr',)
	def __init__(self, op, expr):
		super().__init__(None)
		self.op = op
		self.expr = expr


class Union(AST):
	_fields = ('decls',)
	def __init__(self, name, *decls):
		super().__init__(None)
		self.name = name
		self.decls = decls


class While(AST):
	_fields = ('cond', 'stmt',)
	def __init__(self, cond, stmt):
		super().__init__(None)
		self.cond = cond
		self.stmt = stmt


class WhiteSpace(AST):
	_fields = ()
	def __init__(self, value):
		super().__init__(None)
		self.value = value
