'''
Copyright (c) 2011, Terrence Cole.
All rights reserved.
'''
from melano.c import ast as c


class LLType:
	def __init__(self, hlnode, visitor):
		super().__init__()
		self.visitor = visitor
		self.hlnode = hlnode
		self.hltype = hlnode.get_type() if hlnode else None
		self.name = None #set when we declare


	def declare(self, ctx, quals=[], name=None):
		assert isinstance(ctx, c.TranslationUnit) or not self.visitor.scopes or self.visitor.scope.context == ctx, \
					'Somebody called declare() with a context, rather than a scope.context!'
		assert self.name is None # we can only declare once
		if name:
			self.name = ctx.reserve_name(name)
		else:
			if self.hlnode and hasattr(self.hlnode, 'name'):
				self.name = ctx.reserve_name(self.hlnode.name)
			else:
				self.name = ctx.tmpname()


	def fail(self, typename, error):
		self.visitor.set_exception_str(typename, error)
		self.visitor.capture_error()
		self.visitor.exit_with_exception()


	def fail_if_null(self, ctx, name):
		check = c.If(c.FuncCall(c.ID('unlikely'), c.ExprList(c.UnaryOp('!', c.ID(name)))), c.Compound(), None)
		ctx.add(check)
		with self.visitor.new_context(check.iftrue):
			self.visitor.capture_error()
			self.visitor.exit_with_exception()


	def except_if_null(self, ctx, name, exc_name):
		check = c.If(c.FuncCall(c.ID('unlikely'), c.ExprList(c.UnaryOp('!', c.ID(name)))), c.Compound(), None)
		ctx.add(check)
		with self.visitor.new_context(check.iftrue):
			self.visitor.context.add(c.FuncCall(c.ID('PyErr_SetNone'), c.ExprList(c.ID(exc_name))))
			self.visitor.capture_error()
			self.visitor.exit_with_exception()


	def fail_if_nonzero(self, ctx, name):
		check = c.If(c.FuncCall(c.ID('unlikely'), c.ExprList(c.BinaryOp('!=', c.Constant('integer', 0), c.ID(name)))), c.Compound(), None)
		ctx.add(check)
		with self.visitor.new_context(check.iftrue):
			self.visitor.capture_error()
			self.visitor.exit_with_exception()


	def fail_if_negative(self, ctx, name):
		check = c.If(c.FuncCall(c.ID('unlikely'), c.ExprList(c.BinaryOp('>', c.Constant('integer', 0), c.ID(name)))), c.Compound(), None)
		ctx.add(check)
		with self.visitor.new_context(check.iftrue):
			self.visitor.capture_error()
			self.visitor.exit_with_exception()
