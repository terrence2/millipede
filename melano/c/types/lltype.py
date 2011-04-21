'''
Copyright (c) 2011, Terrence Cole.
All rights reserved.
'''
from melano.c import ast as c


class LLType:
	def __init__(self, hlnode, visitor):
		super().__init__()
		self.v = visitor
		self.hlnode = hlnode
		self.hltype = hlnode.get_type() if hlnode else None
		self.name = None #set when we declare


	def declare(self, *, is_global=False, quals=[], name=None):
		assert self.name is None # we can only declare once
		if is_global:
			fn = self.v.tu.reserve_global_name
			args = ()
		else:
			fn = self.v.scope.ctx.reserve_name
			args = (self.v.tu,)
		if name:
			self.name = fn(name, *args)
		else:
			if self.hlnode and hasattr(self.hlnode, 'name'):
				self.name = fn(self.hlnode.name, *args)
			else:
				assert not is_global
				self.name = self.v.scope.ctx.tmpname(self.v.tu)


	def fail(self, typename, error):
		self.v.set_exception_str(typename, error)
		self.v.capture_error()
		self.v.exit_with_exception()


	def fail_formatted(self, typename, error, *insts):
		self.v.set_exception_format(typename, error, *insts)
		self.v.capture_error()
		self.v.exit_with_exception()


	def fail_if_null(self, name):
		check = self.v.ctx.add(c.If(c.FuncCall(c.ID('unlikely'), c.ExprList(c.UnaryOp('!', c.ID(name)))), c.Compound(), None))
		with self.v.new_context(check.iftrue):
			self.v.capture_error()
			self.v.exit_with_exception()


	def fail_if_error_occurred(self):
		check = self.v.ctx.add(c.If(c.FuncCall(c.ID('PyErr_Occurred'), c.ExprList()), c.Compound(), None))
		with self.v.new_context(check.iftrue):
			self.v.capture_error()
			self.v.exit_with_exception()


	def except_if_null(self, name, exc_name, exc_str=None):
		check = self.v.ctx.add(c.If(c.FuncCall(c.ID('unlikely'), c.ExprList(c.UnaryOp('!', c.ID(name)))), c.Compound(), None))
		with self.v.new_context(check.iftrue):
			if exc_str:
				self.v.ctx.add(c.FuncCall(c.ID('PyErr_SetString'), c.ExprList(c.ID(exc_name), c.Constant('string', exc_str))))
			else:
				self.v.ctx.add(c.FuncCall(c.ID('PyErr_SetNone'), c.ExprList(c.ID(exc_name))))
			self.v.capture_error()
			self.v.exit_with_exception()


	def fail_if_nonzero(self, name):
		check = self.v.ctx.add(c.If(c.FuncCall(c.ID('unlikely'), c.ExprList(c.BinaryOp('!=', c.Constant('integer', 0), c.ID(name)))), c.Compound(), None))
		with self.v.new_context(check.iftrue):
			self.v.capture_error()
			self.v.exit_with_exception()


	def fail_if_negative(self, name):
		check = self.v.ctx.add(c.If(c.FuncCall(c.ID('unlikely'), c.ExprList(c.BinaryOp('>', c.Constant('integer', 0), c.ID(name)))), c.Compound(), None))
		with self.v.new_context(check.iftrue):
			self.v.capture_error()
			self.v.exit_with_exception()

