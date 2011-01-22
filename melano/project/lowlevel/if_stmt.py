'''
Copyright (c) 2011, Terrence Cole.
All rights reserved.
'''
from melano.project.lowlevel.expr import Expr


class LLIf(Expr):
	def __init__(self):
		super().__init__()


	def emit(self, fp, pad):
		fp.write(pad + 'if(')
		super().emit(fp, '')
		fp.write(')')
