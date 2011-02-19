'''
Copyright (c) 2011, Terrence Cole.
All rights reserved.
'''
from melano.c import ast as c


class LLType:
	def __init__(self, name):
		super().__init__()
		self.name = name


	def fail_if_null(self, name, target):
		#decls = [c.FuncCall(c.ID('Py_DECREF'), c.ExprList(c.ID(name))) for name in target.cleanup]
		#decls.append(c.Return(c.ID('NULL')))
		target.add(c.If(c.FuncCall(c.ID('unlikely'), c.ExprList(c.UnaryOp('!', c.ID(name)))), c.Compound(c.Goto('end')), None))

	def fail_if_nonzero(self, name, target):
		#decls = [c.FuncCall(c.ID('Py_DECREF'), c.ExprList(c.ID(name))) for name in target.cleanup]
		#decls.append(c.Return(c.ID('NULL')))
		target.add(c.If(c.FuncCall(c.ID('unlikely'), c.ExprList(c.BinaryOp('!=', c.Constant('integer', 0), c.ID(name)))), c.Compound(c.Goto('end')), None))

