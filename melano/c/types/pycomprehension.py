'''
Copyright (c) 2011, Terrence Cole.
All rights reserved.
'''
from melano.c import ast as c
from melano.c.types.lltype import LLType


class PyComprehensionLL(LLType):
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)

		self.locals_map = {} # {str: inst}

	def prepare_locals(self, context):
		for name, sym in self.hlnode.symbols.items():
			self.locals_map[name] = self.visitor.create_ll_instance(sym)
			self.locals_map[name].declare(self.visitor.scope.context)


	def set_attr_string(self, ctx, attrname, val_inst):
		ctx.add(c.Assignment('=', c.ID(self.locals_map[attrname].name), c.ID(val_inst.name)))


	def get_attr_string(self, ctx, attrname, out_inst):
		ctx.add(c.Assignment('=', c.ID(out_inst.name), c.ID(self.locals_map[attrname].name)))
