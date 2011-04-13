'''
Copyright (c) 2011, Terrence Cole.
All rights reserved.
'''
from melano.c import ast as c
from melano.c.types.lltype import LLType
from melano.c.types.pyobject import PyObjectLL
from melano.hl.nameref import NameRef


class PyComprehensionLL(LLType):
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.locals_map = {} # {str: inst}


	def declare(self, ctx, quals=[], name=None):
		super().declare(ctx, quals, name)
		ctx.add_variable(c.Decl(self.name, PyObjectLL.typedecl(self.name), quals=quals, init=c.ID('NULL')), True)


	def prepare_locals(self, context):
		for name, sym in self.hlnode.symbols.items():
			if isinstance(sym, NameRef): continue # skip refs, only create names created here
			self.locals_map[name] = self.visitor.create_ll_instance(sym)
			self.locals_map[name].declare(self.visitor.scope.context)


	def set_attr_string(self, ctx, attrname, val_inst):
		self.locals_map[attrname].xdecref(ctx)
		val_inst = val_inst.as_pyobject(ctx)
		val_inst.incref(ctx)
		ctx.add(c.Assignment('=', c.ID(self.locals_map[attrname].name), c.ID(val_inst.name)))


	def get_attr_string(self, ctx, attrname, out_inst):
		ctx.add(c.Assignment('=', c.ID(out_inst.name), c.ID(self.locals_map[attrname].name)))
		out_inst.incref(ctx)
