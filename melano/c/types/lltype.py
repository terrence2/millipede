'''
Copyright (c) 2011, Terrence Cole.
All rights reserved.
'''
from melano.c import ast as c


class LLType:
	def __init__(self, hlnode, visitor):
		super().__init__()
		self.v = visitor
		self.hlnode = hlnode
		self.hltype = hlnode.get_type() if hlnode else None
		self.name = None #set when we declare
		self.is_tmp = False # helps controls the lifetime of this instance


	def tmp_incref(self):
		if self.is_tmp:
			#print("ADD   : {}".format(self.name))
			if self in self.v.tmp_free[-1]:
				self.v.tmp_free[-1].remove(self)
			self.v.tmp_used[-1].add(self)

	def tmp_decref(self):
		if self.is_tmp:
			#print("REMOVE: {}".format(self.name))
			self.v.tmp_used[-1].remove(self)
			self.v.tmp_free[-1].add(self)


	def declare_tmp(self, *, name=None):
		'''Note: this steals names, not instances -- although we store the instance, we blow it away here if we overwrite the name'''
		def _find_name():
			# NOTE: ensure these or ordered, so that it is easier to track their re-use at C level
			for prior in sorted(self.v.tmp_free[-1], key=lambda k: k.name):
				if type(prior) is type(self):
					if name is not None and prior.name.startswith(name):
						self.v.tmp_free[-1].remove(prior)
						return prior.name, False
					elif name is None and prior.name.startswith('tmp'):
						self.v.tmp_free[-1].remove(prior)
						return prior.name, False

			if name:
				return self.v.scope.ctx.reserve_name(name, self.v.tu), True
			return self.v.scope.ctx.tmpname(self.v.tu), True

		self.is_tmp = True
		self.name, need_declare = _find_name()
		self.v.tmp_used[-1].add(self)
		#print("DECL  : {}".format(self.name))
		#if self.name == 'tmp5':
		#	import pdb; pdb.set_trace()
		return need_declare


	def declare(self, *, is_global=False, quals=[], name=None):
		assert self.name is None # we can only declare once
		assert (self.hlnode and hasattr(self.hlnode, 'name')) or (name is not None)
		if is_global:
			fn = self.v.tu.reserve_global_name
			args = ()
		else:
			fn = self.v.scope.ctx.reserve_name
			args = (self.v.tu,)
		self.name = fn(name or self.hlnode.name, *args)


	def fail(self, typename, error):
		self.v.set_exception_str(typename, error)
		self.v.capture_error()
		self.v.exit_with_exception()


	def fail_formatted(self, typename, error, *insts):
		self.v.set_exception_format(typename, error, *insts)
		self.v.capture_error()
		self.v.exit_with_exception()


	def fail_if_null(self, name):
		check = self.v.ctx.add(c.If(c.FuncCall(c.ID('unlikely'), c.ExprList(c.UnaryOp('!', c.ID(name)))), c.Compound(), None))
		with self.v.new_context(check.iftrue):
			self.v.capture_error()
			self.v.exit_with_exception()


	def fail_if_error_occurred(self):
		check = self.v.ctx.add(c.If(c.FuncCall(c.ID('PyErr_Occurred'), c.ExprList()), c.Compound(), None))
		with self.v.new_context(check.iftrue):
			self.v.capture_error()
			self.v.exit_with_exception()


	def except_if_null(self, name, exc_name, exc_str=None):
		check = self.v.ctx.add(c.If(c.FuncCall(c.ID('unlikely'), c.ExprList(c.UnaryOp('!', c.ID(name)))), c.Compound(), None))
		with self.v.new_context(check.iftrue):
			if exc_str:
				self.v.ctx.add(c.FuncCall(c.ID('PyErr_SetString'), c.ExprList(c.ID(exc_name), c.Constant('string', exc_str))))
			else:
				self.v.ctx.add(c.FuncCall(c.ID('PyErr_SetNone'), c.ExprList(c.ID(exc_name))))
			self.v.capture_error()
			self.v.exit_with_exception()


	def fail_if_nonzero(self, name):
		check = self.v.ctx.add(c.If(c.FuncCall(c.ID('unlikely'), c.ExprList(c.BinaryOp('!=', c.Constant('integer', 0), c.ID(name)))), c.Compound(), None))
		with self.v.new_context(check.iftrue):
			self.v.capture_error()
			self.v.exit_with_exception()


	def fail_if_negative(self, name):
		check = self.v.ctx.add(c.If(c.FuncCall(c.ID('unlikely'), c.ExprList(c.BinaryOp('>', c.Constant('integer', 0), c.ID(name)))), c.Compound(), None))
		with self.v.new_context(check.iftrue):
			self.v.capture_error()
			self.v.exit_with_exception()

