'''
Copyright (c) 2011, Terrence Cole.
All rights reserved.
'''
from melano.project.lowlevel.block import LLBlock

class LLFunction(LLBlock):
	def __init__(self, name, args, arg_types, ret_type, *args_, **kwargs):
		super().__init__(*args_, **kwargs)
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
		fp.write(pad + self.sig + ' ')
		super().emit(fp, pad)


class LLModuleFunction(LLFunction):
	'''At the lowlevel this is a normal function, at a high-level
		this is the module-initialization / run.'''
	def __init__(self, name, *args, **kwargs):
		super().__init__(name, [], [], 'void', *args, **kwargs)


	def import_(self, module:str):
		'''In addition to doing the import, we need to expose the name of the module at the top-level.'''
		name = super().import_(module)
		self.target.add_static('PyObject*', name)
