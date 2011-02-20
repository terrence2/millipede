'''
Copyright (c) 2011, Terrence Cole.
All rights reserved.
'''
from melano.c import ast as c


class LLType:
	def __init__(self, name):
		super().__init__()
		self.name = name


	def fail_if_null(self, ctx, name):
		ctx.add(c.If(c.FuncCall(c.ID('unlikely'), c.ExprList(c.UnaryOp('!', c.ID(name)))), c.Compound(c.Goto('end')), None))


	def fail_if_nonzero(self, ctx, name):
		ctx.add(c.If(c.FuncCall(c.ID('unlikely'), c.ExprList(c.BinaryOp('!=', c.Constant('integer', 0), c.ID(name)))), c.Compound(c.Goto('end')), None))


	def fail_if_negative(self, ctx, name):
		ctx.add(c.If(c.FuncCall(c.ID('unlikely'), c.ExprList(c.BinaryOp('>', c.Constant('integer', 0), c.ID(name)))), c.Compound(c.Goto('end')), None))
