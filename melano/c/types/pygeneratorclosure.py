'''
Copyright (c) 2011, Terrence Cole.
All rights reserved.
'''
from melano.c import ast as c
from melano.c.types.integer import CIntegerLL
from melano.c.types.pyclosure import PyClosureLL
from melano.c.types.pygenerator import PyGeneratorLL
from melano.c.types.pyobject import PyObjectLL
from melano.c.types.pystring import PyStringLL


class PyGeneratorClosureLL(PyClosureLL, PyGeneratorLL):
	'''
	For the most part, generators and closures do not intersect, except during handling of arg loading 
	in the runner, where we need to copy into the frame from the gen_args pointer, rather than off the C stack.
	'''
	def runner_load_args(self, args, vararg, kwonlyargs, kwarg):
		# put all args into the new MelanoLocals array, no further decl required for locals
		args = self._buildargs(args, vararg, kwonlyargs, kwarg)
		for offset, arg in enumerate(args, self.ARGS_INDEX):
			self.v.ctx.add(c.Comment("set arg '{}'".format(str(arg.arg))))
			i, j = self.locals_map[str(arg.arg)]
			tgt = c.ArrayRef(c.StructRef(c.ArrayRef(c.ID(self.stack_name), c.Constant('integer', i)), '->', c.ID('locals')), c.Constant('integer', j))
			src = c.ArrayRef(c.ID(self.args_name), c.Constant('integer', offset))
			self.v.ctx.add(c.Assignment('=', tgt, src))

