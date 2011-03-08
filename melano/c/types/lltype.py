'''
Copyright (c) 2011, Terrence Cole.
All rights reserved.
'''
from melano.c import ast as c


class LLType:
	def __init__(self, hlnode):
		super().__init__()
		self.hlnode = hlnode
		self.hltype = hlnode.get_type() if hlnode else None
		self.name = None #set when we declare


	def declare(self, ctx, quals=[], name=None):
		assert isinstance(ctx, c.TranslationUnit) or not ctx._visitor.scopes or ctx._visitor.scope.context == ctx
		assert self.name is None # we can only declare once
		if name:
			self.name = ctx.reserve_name(name)
		else:
			if self.hlnode and hasattr(self.hlnode, 'name'):
				self.name = ctx.reserve_name(self.hlnode.name)
			else:
				self.name = ctx.tmpname()


	@staticmethod
	def capture_error(ctx):
		filename = ctx._visitor.hl_module.filename
		try: context = ctx._visitor.scope.owner.name
		except IndexError: context = '<module>'
		st = ctx._visitor._current_node.start
		end = ctx._visitor._current_node.end

		if st[0] == end[0]: # one line only
			src = ctx._visitor.hl_module.get_source_line(st[0])
			rng = (st[1], end[1])
		else:
			# if we can't fit the full error context on one line, also print the number of lines longer it goes and the ending column
			src = ctx._visitor.hl_module.get_source_line(st[0]) + ' => (+{},{})'.format(end[0] - st[0], end[1])
			rng = (st[1], len(src))
		src = src.strip().replace('"', '\\"')

		return c.FuncCall(c.ID('__err_capture__'), c.ExprList(
						c.Constant('string', filename), c.Constant('integer', st[0]), c.ID('__LINE__'), c.Constant('string', context),
						c.Constant('string', src), c.Constant('integer', rng[0]), c.Constant('integer', rng[1])))


	@classmethod
	def fail(cls, ctx, error):
		ctx.add(cls.capture_error(ctx))
		ctx.add(c.Goto('end'))


	def fail_if_null(self, ctx, name):
		ctx.add(c.If(c.FuncCall(c.ID('unlikely'), c.ExprList(c.UnaryOp('!', c.ID(name)))), c.Compound(
																		self.capture_error(ctx),
																		c.Goto('end')), None))


	def fail_if_nonzero(self, ctx, name):
		ctx.add(c.If(c.FuncCall(c.ID('unlikely'), c.ExprList(c.BinaryOp('!=', c.Constant('integer', 0), c.ID(name)))), c.Compound(
																		self.capture_error(ctx),
																		c.Goto('end')), None))


	def fail_if_negative(self, ctx, name):
		ctx.add(c.If(c.FuncCall(c.ID('unlikely'), c.ExprList(c.BinaryOp('>', c.Constant('integer', 0), c.ID(name)))), c.Compound(
																		self.capture_error(ctx),
																		c.Goto('end')), None))
