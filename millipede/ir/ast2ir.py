'''
Copyright (c) 2011, Terrence Cole.
All rights reserved.
'''
from contextlib import contextmanager
from millipede.hl.nodes.builtins import Builtins
from millipede.hl.nodes.entity import Entity
from millipede.hl.nodes.module import MpModule
from millipede.hl.types.pystring import PyStringType
from millipede.ir.opcodes import Intermediate
from millipede.lang.visitor import ASTVisitor
from millipede.py import ast as py
import collections
import itertools
import logging
import millipede.ir.opcodes as opcode
import pdb



class Ast2Ir(ASTVisitor):
	'''Reduces one module into an IR representation.  Calling visit produces a table mapping names (functions, 
		class definitions, the module itself, etc.) to IR code that implements the given AST.'''
	def __init__(self, project):
		super().__init__()

		# a mapping from frame names to the frame structures themselves
		# NOTE: This is the visitor's output.
		self.frames = {}

		# the current frame
		self.ctx = None

		# provides unique names for our internal variables
		self._tmpnum = itertools.count(0)
		self._labelnum = collections.Counter()


	@contextmanager
	def new_frame(self, scope):
		self.frames[scope.owner.global_c_name] = scope
		prior, self.ctx = self.ctx, scope
		yield
		self.ctx = prior


	def tmpname(self):
		while True:
			nm = '_tmp' + str(next(self._tmpnum))
			try:
				self.ctx.lookup(nm)
			except KeyError:
				return Intermediate(nm)


	#FIXME: move to scope, since we have it there anyway?
	def labelname(self, base):
		name = base + str(self._labelnum[base])
		self._labelnum[base] += 1
		return name


	def generic_visit(self, node):
		logging.warning('Skipping: ' + str(node))
		return super().generic_visit(node)


	def visit_nodelist(self, nodes):
		super().visit_nodelist(nodes)
		if self.ctx._ready_label:
			self.ctx.instr(opcode.NOP(None))


	def cleanup_intermediates(self, ops):
		'''Insert decrefs for intermediate nodes.
			FIXME: this will probably mess with reordering in undesirable ways and will need to be moved later.
		'''
		seen = set()
		new_ops = collections.deque()
		for op in reversed(ops):
			tmps = [i for i in op.operands if isinstance(i, Intermediate)]
			if isinstance(op.target, Intermediate):
				tmps += [op.target]

			for tmp in tmps:
				s_tmp = str(tmp)
				if s_tmp not in seen:
					new_ops.appendleft(opcode.DECREF(tmp, None))
					seen.add(s_tmp)

			new_ops.appendleft(op)

		return list(new_ops)


	def _store_any(self, node, to_store):
		'''Store a temporary back into "real" storage.
			node: a hl.Name, Attr, etc representing the real name to store to
			to_store: the temporary name the value is currently stored in
		'''
		if isinstance(node, py.Name):
			if isinstance(node.hl.parent, MpModule):
				self.ctx.instr(opcode.STORE_GLOBAL(node.hl, to_store, node))
			else:
				self.ctx.instr(opcode.STORE_LOCAL(node.hl, to_store, node))
		elif isinstance(node, py.Attribute):
			lhs = self._load_any(node.value)
			self.ctx.instr(opcode.STORE_ATTR(lhs, str(node.attr), to_store, node))
		else:
			raise NotImplementedError


	def _load_any(self, node):
		tgt = self.tmpname()
		if isinstance(node, py.Name):
			name = self.ctx.lookup(str(node))
			#if isinstance(name.parent, Builtins):
			#	self.ctx.instr(opcode.LOAD_BUILTIN(tgt, node.hl, node))
			#elif isinstance(name.parent, MpModule):
			#	self.ctx.instr(opcode.LOAD_GLOBAL(tgt, node.hl, node))
			if isinstance(name.parent, MpModule):
				self.ctx.instr(opcode.LOAD_GLOBAL_OR_BUILTIN(tgt, node.hl, node))
			else:
				self.ctx.instr(opcode.LOAD_LOCAL(tgt, node.hl, node))
		else:
			pdb.set_trace()
			raise NotImplementedError
		return tgt


	#### FRAMES
	def visit_Module(self, node):
		props = [('__doc__', PyStringType.dequote(node.docstring or '""')),
				('__file__', node.hl.filename),
				('__name__', node.hl.name)]
		with self.new_frame(node.hl):
			for n, v in props:
				tmp = self.tmpname()
				self.ctx.instr(opcode.LOAD_CONST(tmp, v, None))
				self.ctx.instr(opcode.STORE_GLOBAL(node.hl.symbols[n], tmp, None))

			# body
			self.visit_nodelist(node.body)

			# return self
			node.hl.instr(opcode.RETURN_VALUE(node.hl, None))

			# insert cleanup code
			node.hl._instructions = self.cleanup_intermediates(node.hl._instructions)


	#def visit_Class(self, node):


	def visit_FunctionDef(self, node):
		#('args')

		# create the function
		tgt = self.tmpname()
		self.ctx.instr(opcode.MAKE_FUNCTION(tgt, node.hl, node))

		# store the docstring
		ds_tmp = self.tmpname()
		self.ctx.instr(opcode.LOAD_CONST(ds_tmp, PyStringType.dequote(node.docstring or '""'), None))
		self.ctx.instr(opcode.STORE_ATTR(tgt, '__doc__', ds_tmp, None))

		# setup and store keywords

		# setup and store annotations, including returns
		annotations = []
		for arg in (node.args.args or []):
			if arg.annotation:
				tmp_name = self.tmpname()
				self.ctx.instr(opcode.LOAD_CONST(tmp_name, str(arg.arg), arg.arg))
				tmp_value = self.visit(arg.annotation)
				annotations.extend((tmp_name, tmp_value))
		if node.returns:
			tmp_name = self.tmpname()
			self.ctx.instr(opcode.LOAD_CONST(tmp_name, 'return', node.returns))
			tmp_value = self.visit(node.returns)
			annotations.extend((tmp_name, tmp_value))
		ann_name = self.tmpname()
		self.ctx.instr(opcode.MAKE_DICT(ann_name, *(annotations + [None])))
		self.ctx.instr(opcode.STORE_ATTR(tgt, '__annotations__', ann_name, None))

		# chain all decorators
		for deco in (node.decorator_list or []):
			tmp = self.visit(deco)
			tgt_next = self.tmpname()
			self.ctx.instr(opcode.CALL_GENERIC(tgt_next, tmp, [tgt], None, None, None, deco))
			self.ctx.prepare_label(self.labelname('ret'))
			tgt = tgt_next

		# store after modifying with decorators
		self._store_any(node.name, tgt)

		# Create and populate the new frame object for the function
		with self.new_frame(node.hl):
			self.visit_nodelist(node.body)

			# automatically insert a return None at the end
			if not self.ctx._instructions or not isinstance(self.ctx._instructions[-1], opcode.RETURN_VALUE):
				tgt = self.tmpname()
				self.ctx.instr(opcode.LOAD_CONST(tgt, None, None))
				self.ctx.instr(opcode.RETURN_VALUE(tgt, node))

			# insert cleanup code
			node.hl._instructions = self.cleanup_intermediates(node.hl._instructions)


	#### INSTRUCTIONS
	def visit_Assign(self, node):
		nm = self.visit(node.value)
		for tgt in node.targets:
			self._store_any(tgt, nm)


	def visit_BinOp(self, node):
		lhs = self.visit(node.left)
		rhs = self.visit(node.right)
		tgt = self.tmpname()
		if node.op == py.BitOr: cls = opcode.BINARY_OR
		elif node.op == py.BitXor: cls = opcode.BINARY_XOR
		elif node.op == py.BitAnd: cls = opcode.BINARY_AND
		elif node.op == py.LShift: cls = opcode.BINARY_LSHIFT
		elif node.op == py.RShift: cls = opcode.BINARY_RSHIFT
		elif node.op == py.Add: cls = opcode.BINARY_ADD
		elif node.op == py.Sub: cls = opcode.BINARY_SUBTRACT
		elif node.op == py.Mult: cls = opcode.BINARY_MULTIPLY
		elif node.op == py.Div: cls = opcode.BINARY_TRUE_DIVIDE
		elif node.op == py.FloorDiv: cls = opcode.BINARY_FLOOR_DIVIDE
		elif node.op == py.Mod: cls = opcode.BINARY_MODULO
		elif node.op == py.Pow: cls = opcode.BINARY_POWER
		self.ctx.instr(cls(tgt, lhs, rhs, node))
		return tgt


	def visit_Call(self, node):
		func = self.visit(node.func)

		args = []
		if node.args:
			for arg in node.args:
				args.append(self.visit(arg))

		starargs = None if not node.starargs else self.visit(node.starargs)

		keywords = {}
		if node.keywords:
			for kw in node.keywords:
				keywords[str(kw.name)] = self.visit(kw.value)

		kwargs = None if not node.kwargs else self.visit(node.kwargs)

		rv = self.tmpname()
		self.ctx.instr(opcode.CALL_GENERIC(rv, func, args, starargs, keywords, kwargs, node))
		self.ctx.prepare_label(self.labelname('ret'))
		return rv


	#def visit_Compare(self, node):
	#	pdb.set_trace()
	#	lhs = self.visit(node.left)
	#	rhs = self.visit(node.comparators[0])
	#	tgt = self.tmpname()
	#	self.ctx.instr(COMPARE(tgt, lhs, node.ops[0], rhs, node))
	#	for op, comp in zip(node.ops[1:], node.comparators[1:]):
	#		BRANCH
	#		prepare label
	#		lhs = rhs
	#		rhs = self.visit(comp)
	#	return tgt



	def visit_If(self, node):
		label_true = self.labelname('if')
		label_false = self.labelname('ifelse') #NOTE: even if we don't use it, pump the index so we don't get mismatched ever
		label_end = self.labelname('ifend')

		nm = self.visit(node.test)
		self.ctx.instr(opcode.BRANCH(nm, label_true, label_false, node))

		self.ctx.prepare_label(label_true)
		self.visit_nodelist(node.body)
		self.ctx.instr(opcode.JUMP(label_end, None))
		if node.orelse:
			self.ctx.prepare_label(label_false)
			self.visit_nodelist(node.orelse)
			self.ctx.instr(opcode.JUMP(label_end, None))
		self.ctx.label_instr(label_end, opcode.NOP(None))



	def visit_Import(self, node):
		for alias in node.names:
			tgt = self.tmpname()
			self.ctx.instr(opcode.IMPORT_NAME(tgt, alias.name, alias.name))
			self.ctx.prepare_label(self.labelname('ret'))
			store = alias.asname if alias.asname else alias.name
			self._store_any(store, tgt)


	def visit_Attribute(self, node):
		tmp_name = self.visit(node.value)
		if node.ctx in (py.Load, py.Aug):
			out_name = self.tmpname()
			self.ctx.instr(opcode.LOAD_ATTR(out_name, tmp_name, str(node.attr), node))
			return out_name
		else:
			raise NotImplementedError


	def visit_Name(self, node):
		if node.ctx in (py.Load, py.Aug):
			return self._load_any(node)
		else:
			raise NotImplementedError


	def visit_Pass(self, node):
		self.ctx.instr(opcode.NOP(node))


	def visit_Return(self, node):
		if node.value:
			tgt = self.visit(node.value)
		else:
			tgt = self.tmpname()
			self.ctx.instr(opcode.LOAD_CONST(tgt, None, node))
		self.ctx.instr(opcode.RETURN_VALUE(tgt, node))


	#### CONTAINERS
	#def visit_Tuple(self, node):
	#	srcs = [self.visit(e) for e in node.elts]
	#	tgt = self.tmpname()
	#	self.ctx.instr(BUILD_TUPLE(tgt, *(srcs + [node])))
	#	return tgt


	#### CONSTANTS
	def visit_Num(self, node):
		tgt = self.tmpname()
		self.ctx.instr(opcode.LOAD_CONST(tgt, node.n, node))
		return tgt

	def visit_Str(self, node):
		tgt = self.tmpname()
		self.ctx.instr(opcode.LOAD_CONST(tgt, PyStringType.dequote(node.s), node))
		return tgt
