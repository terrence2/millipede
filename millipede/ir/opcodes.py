'''
Copyright (c) 2011, Terrence Cole.
All rights reserved.
'''
from millipede.hl.nodes.entity import Entity
import itertools


class Intermediate(Entity):
	'''A name in the IR.  In addition to the name and entity properties, this has a slot for the ll inst at emission time.'''
	def __init__(self, name:str, *args, **kwargs):
		super().__init__(None, *args, **kwargs)
		self.name = name
		self.ll = None

	def __str__(self):
		return '|' + self.name + '|'



class Op:
	def __init__(self, ast):
		self._ast = ast

		self.label = None
		self.target = None
		self.operands = [] # [str]

	def format(self, trailer=None):
		if self.label: out = '{:>10}:  '.format(self.label)
		else: out = ' ' * 10 + '   '
		if self.target:
			out += '{:16}{:12} <- {}'.format(self.__class__.__name__, self.target, trailer or '')
		else:
			out += '{:16}{}'.format(self.__class__.__name__, trailer or '')
		return out

	def __repr__(self):
		return '<{}>'.format(self.__class__.__name__)


class BinOp(Op):
	PRETTY_FMT = '?'

	def __init__(self, tgt, lhs, rhs, *args, **kws):
		super().__init__(*args, **kws)
		self.target = tgt
		self.operands = (lhs, rhs)

	def format(self):
		return super().format('{} {} {}'.format(self.operands[0], self.PRETTY_FMT, self.operands[1]))


# Arithmetic Ops
class BINARY_ADD(BinOp): PRETTY_FMT = '+'
class BINARY_FLOOR_DIVIDE(BinOp): PRETTY_FMT = '//'
class BINARY_TRUE_DIVIDE(BinOp): PRETTY_FMT = '/'
class BINARY_MODULO(BinOp): PRETTY_FMT = '%'
class BINARY_MULTIPLY(BinOp): PRETTY_FMT = '*'
class BINARY_POWER(BinOp): PRETTY_FMT = '**'
class BINARY_SUBTRACT(BinOp): PRETTY_FMT = '-'
class BINARY_SUBSCRIPT(BinOp): PRETTY_FMT = '[]'
# Bit Ops
class BINARY_LSHIFT(BinOp): PRETTY_FMT = '<<'
class BINARY_RSHIFT(BinOp):  PRETTY_FMT = '>>'
class BINARY_AND(BinOp): PRETTY_FMT = '&'
class BINARY_XOR(BinOp): PRETTY_FMT = '^'
class BINARY_OR(BinOp): PRETTY_FMT = '|'


class BRANCH(Op):
	def __init__(self, test, label_true, label_false, *args, **kws):
		super().__init__(*args, **kws)
		self.operands = (test,)
		self.label_true = label_true
		self.label_false = label_false

	def format(self):
		return super().format('{} >> {} >> {}'.format(self.operands[0], self.label_true, self.label_false))


class JUMP(Op):
	def __init__(self, label_target, *args, **kws):
		super().__init__(*args, **kws)
		self.label_target = label_target

	def format(self):
		return super().format('>> {}'.format(self.label_target))


class RETURN_VALUE(Op):
	'''Like an external jump with some extra semantics.'''
	def __init__(self, value, *args, **kws):
		super().__init__(*args, **kws)
		self.operands = (value,)

	def format(self):
		return super().format(self.operands[0])


class NOP(Op):
	'''Does nothing, but can take a label.'''


class DECREF(Op):
	def __init__(self, value, *args, **kws):
		super().__init__(*args, **kws)
		self.operands = (value,)

	def format(self):
		return super().format(self.operands[0])


class CALL_GENERIC(Op):
	'''Contains all arg sets internally.  Generally, this will get replaced by some more specific calling convention
		that unrolls the args into manual create_tuple/dict etc, depending on our eventual type information at the 
		call site.'''
	def __init__(self, target, func, args, stararg, keywords, kwarg, *args_, **kws_):
		super().__init__(*args_, **kws_)
		self.target = target
		flat_kw = list(itertools.chain.from_iterable(zip([k for k in keywords.keys()], [v for v in keywords.values()])))
		self.operands = tuple([func] + args + [stararg] + flat_kw + [kwarg])
		self.func = func
		self.args = args
		self.stararg = stararg
		self.keywords = keywords
		self.kwarg = kwarg

	def format(self):
		a = ', '.join([str(a) for a in (self.args or [])]) or None
		b = str(self.stararg) if self.stararg else None
		c = {str(k): str(self.keywords[k]) for k in (self.keywords or {})}
		d = str(self.kwarg) if self.kwarg else None
		return super().format('{}({}, *{}, {}, **{})'.format(str(self.func), a, b, c, d))


class IMPORT_NAME(Op):
	def __init__(self, target, modname, *args, **kws):
		super().__init__(*args, **kws)
		self.target = target
		self.operands = (modname,)

	def format(self):
		return super().format(self.operands[0])


class MAKE_FUNCTION(Op):
	def __init__(self, target, scope, *args, **kws):
		super().__init__(*args, **kws)
		self.target = target
		self.operands = (scope,)

	def format(self):
		return super().format(self.operands[0].owner.python_name)


class MAKE_DICT(Op):
	def __init__(self, target, *args, **kws):
		super().__init__(*(args[-1:]), **kws)
		self.target = target
		self.operands = tuple(args[:-1])

	def format(self):
		data = ','.join([str(o) for o in self.operands])
		return super().format('{' + data + '}')


class LOAD_CONST(Op):
	def __init__(self, target, v, *args, **kws):
		super().__init__(*args, **kws)
		self.target = target
		self.v = v

	def format(self):
		return super().format('{} <{}>'.format(self.v, type(self.v).__name__))


class STORE_GLOBAL(Op):
	def __init__(self, hl_target, name, *args, **kws):
		super().__init__(*args, **kws)
		self.target = hl_target
		self.operands = (name,)

	def format(self):
		return super().format('{}'.format(str(self.operands[0])))


class STORE_LOCAL(Op):
	def __init__(self, hl_target, name, *args, **kws):
		super().__init__(*args, **kws)
		self.hl_target = hl_target
		self.operands = (name,)

	def format(self):
		return super().format('{:12} <- {}'.format(str(self.hl_target), str(self.operands[0])))


class STORE_ATTR(Op):
	def __init__(self, tmp_target, attrname, to_store, *args, **kws):
		super().__init__(*args, **kws)
		self.operands = (tmp_target, attrname, to_store)

	def format(self):
		return super().format('{:12} <- {}'.format(str(self.operands[0]) + '.' + str(self.operands[1]), str(self.operands[2])))


class LOAD_ATTR(Op):
	def __init__(self, target, base, attrname, *args, **kws):
		super().__init__(*args, **kws)
		self.target = target
		self.operands = (base, attrname)

	def format(self):
		return super().format('{:12}'.format(str(self.operands[0]) + '.' + str(self.operands[1])))


class LOAD_BUILTIN(Op):
	def __init__(self, target, hl_source, *args, **kws):
		super().__init__(*args, **kws)
		self.target = target
		self.hl_source = hl_source

	def format(self):
		return super().format('{}'.format(str(self.hl_source.deref())))


class LOAD_GLOBAL(Op):
	def __init__(self, target, hl_source, *args, **kws):
		super().__init__(*args, **kws)
		self.target = target
		self.hl_source = hl_source

	def format(self):
		return super().format('{}'.format(str(self.hl_source.deref())))


class LOAD_GLOBAL_OR_BUILTIN(Op):
	def __init__(self, target, hl_source, *args, **kws):
		super().__init__(*args, **kws)
		self.target = target
		self.hl_source = hl_source

	def format(self):
		return super().format('{}'.format(str(self.hl_source.deref())))


class LOAD_LOCAL(Op):
	def __init__(self, target, hl_source, *args, **kws):
		super().__init__(*args, **kws)
		self.target = target
		self.hl_source = hl_source

	def format(self):
		return super().format('{}'.format(str(self.hl_source.deref())))

