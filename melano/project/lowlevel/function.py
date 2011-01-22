'''
Copyright (c) 2011, Terrence Cole.
All rights reserved.
'''
from melano.project.lowlevel.block import LLBlock

class LLFunction(LLBlock):
	def __init__(self, name, args, arg_types, ret_type):
		self.name = name
		self.args = args
		self.arg_types = arg_types
		self.ret_type = ret_type

		args_str = ["{} {}".format(t, a) for a, t in zip(args, arg_types)]
		args = ", ".join(args_str)
		self.sig = "{} {}({})".format(ret_type, name, args)

		self.stmts = []


	def emit_prototype(self, fp, pad):
		fp.write(pad + self.sig + ';')


	def emit(self, fp, pad):
		fp.write(pad + self.sig)
		super().emit(fp, pad)
