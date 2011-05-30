'''
Copyright (c) 2011, Terrence Cole.
All rights reserved.
'''

class Op:
	def __init__(self, ast):
		self.ast = ast

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



class CALL_FUNCTION(Op):
	def __init__(self, target, func, args, stararg, keywords, kwarg, *args_, **kws_):
		super().__init__(*args_, **kws_)
		self.target = target
		self.func = func
		self.args = args
		self.stararg = stararg
		self.keywords = keywords
		self.kwarg = kwarg

	def format(self):
		return super().format('{}({}, {}, *{}, **{})'.format(self.func, self.args, self.keywords, self.stararg, self.kwarg))


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
		self.hl_target = hl_target
		self.operands = (name,)

	def format(self):
		return super().format('{:12} <- {}'.format(str(self.hl_target), self.operands[0]))


class STORE_LOCAL(Op):
	def __init__(self, hl_target, name, *args, **kws):
		super().__init__(*args, **kws)
		self.hl_target = hl_target
		self.operands = (name,)

	def format(self):
		return super().format('{:12} <- {}'.format(str(self.hl_target), self.operands[0]))


class LOAD_GLOBAL(Op):
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

