'''
Copyright (c) 2011, Terrence Cole.
All rights reserved.
'''
from contextlib import contextmanager
from millipede.hl.nodes.builtins import Builtins
from millipede.hl.nodes.entity import Entity
from millipede.hl.nodes.module import MpModule
from millipede.hl.types.integer import CIntegerType
from millipede.hl.types.pyinteger import PyIntegerType
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
				if tmp.no_cleanup: continue
				s_tmp = str(tmp)
				if s_tmp not in seen:
					new_ops.appendleft(opcode.DECREF(tmp, None))
					seen.add(s_tmp)

					# if the statement we insert in front of is labeled, move the label left to the inserted instr
					if len(new_ops) > 1 and new_ops[1].label:
						new_ops[0].label = new_ops[1].label
						new_ops[1].label = None

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
		elif isinstance(node, (py.Tuple, py.List)):
			for i, elt in enumerate(node.elts):
				offset = self.tmpname()
				self.ctx.instr(opcode.LOAD_CONST(offset, i, None))
				tmp = self.tmpname()
				self.ctx.instr(opcode.LOAD_ITEM(tmp, to_store, offset, None))
				self._store_any(elt, tmp)
		elif isinstance(node, py.Subscript):
			lhs = self._load_any(node.value)
			if isinstance(node.slice, py.Slice):
				lower = self.visit(node.slice.lower)
				upper = self.visit(node.slice.upper)
				step = self.visit(node.slice.step)
				slice = self.tmpname()
				self.ctx.instr(opcode.BUILD_SLICE(slice, lower, upper, step, node.slice))
			else:
				slice = self.visit(node.slice)
			self.ctx.instr(opcode.STORE_ITEM(lhs, slice, to_store, node))
		else:
			raise NotImplementedError(str(type(node)))


	def _load_any(self, node):
		tgt = self.tmpname()
		if isinstance(node, py.Name):
			name = self.ctx.lookup(str(node))
			if isinstance(name.parent, MpModule):
				self.ctx.instr(opcode.LOAD_GLOBAL_OR_BUILTIN(tgt, node.hl, node))
			else:
				self.ctx.instr(opcode.LOAD_LOCAL(tgt, node.hl, node))
		elif isinstance(node, py.Attribute):
			lhs = self._load_any(node.value)
			tgt = self.tmpname()
			self.ctx.instr(opcode.LOAD_ATTR(tgt, lhs, str(node.attr), node))
		elif isinstance(node, py.Subscript):
			base = self._load_any(node.value)
			tgt = self.tmpname()
			if isinstance(node.slice, py.Slice):
				lower = self.visit(node.slice.lower)
				upper = self.visit(node.slice.upper)
				step = self.visit(node.slice.step)
				slice = self.tmpname()
				self.ctx.instr(opcode.BUILD_SLICE(slice, lower, upper, step, node.slice))
			else:
				slice = self.visit(node.slice)
			self.ctx.instr(opcode.LOAD_ITEM(tgt, base, slice, node))
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

		# setup and store defaults
		defaults = []
		for default in (node.args.defaults or []):
			defaults.append(self.visit(default))
		tmp = self.tmpname()
		self.ctx.instr(opcode.BUILD_TUPLE(tmp, *(defaults + [None])))
		self.ctx.instr(opcode.STORE_ATTR(tgt, '__defaults__', tmp, None))

		# setup and store keyword defaults
		if node.args.kw_defaults:
			kwdefaults = []
			for arg, kwdefault in zip(node.args.kwonlyargs, node.args.kw_defaults):
				tmp_name = self.tmpname()
				self.ctx.instr(opcode.LOAD_CONST(tmp_name, str(arg.arg), node.returns))
				kwdefaults.extend((tmp_name, self.visit(kwdefault)))
			tmp = self.tmpname()
			self.ctx.instr(opcode.BUILD_DICT(tmp, *(kwdefaults + [None])))
			self.ctx.instr(opcode.STORE_ATTR(tgt, '__kwdefaults__', tmp, None))

		# setup and store annotations, including returns, and for star and kw args
		annotations = []
		def _annotate(name, vnode):
			tmp_name = self.tmpname()
			self.ctx.instr(opcode.LOAD_CONST(tmp_name, name, None))
			tmp_value = self.visit(vnode)
			annotations.extend((tmp_name, tmp_value))
		for arg in (node.args.args or []) + (node.args.kwonlyargs or []):
			if arg.annotation: _annotate(str(arg.arg), arg.annotation)
		if node.returns: _annotate('return', node.returns)
		if node.args.varargannotation: _annotate(str(node.args.vararg), node.args.varargannotation)
		if node.args.kwargannotation: _annotate(str(node.args.kwarg), node.args.kwargannotation)
		ann_name = self.tmpname()
		self.ctx.instr(opcode.BUILD_DICT(ann_name, *(annotations + [None])))
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
	def visit_AugAssign(self, node):
		lhs = self._load_any(node.target)
		rhs = self.visit(node.value)
		tgt = self.tmpname()
		if node.op == py.BitOr: cls = opcode.INPLACE_OR
		elif node.op == py.BitXor: cls = opcode.INPLACE_XOR
		elif node.op == py.BitAnd: cls = opcode.INPLACE_AND
		elif node.op == py.LShift: cls = opcode.INPLACE_LSHIFT
		elif node.op == py.RShift: cls = opcode.INPLACE_RSHIFT
		elif node.op == py.Add: cls = opcode.INPLACE_ADD
		elif node.op == py.Sub: cls = opcode.INPLACE_SUBTRACT
		elif node.op == py.Mult: cls = opcode.INPLACE_MULTIPLY
		elif node.op == py.Div: cls = opcode.INPLACE_TRUE_DIVIDE
		elif node.op == py.FloorDiv: cls = opcode.INPLACE_FLOOR_DIVIDE
		elif node.op == py.Mod: cls = opcode.INPLACE_MODULO
		elif node.op == py.Pow: cls = opcode.INPLACE_POWER
		else: raise NotImplementedError("Unknown augop: {}".format(node.op))
		self.ctx.instr(cls(tgt, lhs, rhs, node))
		self._store_any(node.target, tgt)


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
		else: raise NotImplementedError("Unknown binop: {}".format(node.op))
		self.ctx.instr(cls(tgt, lhs, rhs, node))
		return tgt


	### GLOBAL BRANCH
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
				keywords[str(kw.keyword)] = self.visit(kw.value)

		kwargs = None if not node.kwargs else self.visit(node.kwargs)

		rv = self.tmpname()
		self.ctx.instr(opcode.CALL_GENERIC(rv, func, args, starargs, keywords, kwargs, node))
		self.ctx.prepare_label(self.labelname('ret'))
		return rv

	def visit_Import(self, node):
		for alias in node.names:
			tgt = self.tmpname()
			self.ctx.instr(opcode.IMPORT_NAME(tgt, alias.name, alias.name))
			self.ctx.prepare_label(self.labelname('ret'))
			store = alias.asname if alias.asname else alias.name
			self._store_any(store, tgt)

	def visit_ImportFrom(self, node):
		raise NotImplementedError("ImportFrom")


	### LOCAL BRANCH
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


	def visit_Try(self, node):
		start_label = self.labelname('try')
		except_label = self.labelname('except')
		orelse_label = self.labelname('noexcept')
		finally_label = self.labelname('finally')
		fail_label = self.labelname('tryfail')
		end_label = self.labelname('tryend')

		#### TRY BB ####
		# Note: all blocks end with a branch and start with a label; even though this should flow normally from the
		#	prior instruction into the try block, we need to split it up with a jump/label pair because every basic-block
		#	should have only a single exception handler target.
		self.ctx.instr(opcode.JUMP(start_label, None))
		self.ctx.prepare_label(start_label)

		# setup compiler to set the target for subsequent runtime failures
		if node.finallybody:
			self.ctx.instr(opcode.SETUP_FINALLY(finally_label, None))
		if node.handlers:
			self.ctx.instr(opcode.SETUP_EXCEPT(except_label, None))

		# emit code for the body
		self.visit_nodelist(node.body)

		# clear the except handler (but not the finally handler)
		if node.handlers:
			self.ctx.instr(opcode.END_EXCEPT(except_label, None))

		# if we make it here, then we want to jump past the exception handler bits
		if node.orelse:
			self.ctx.instr(opcode.JUMP(orelse_label, None))
		elif node.finallybody:
			self.ctx.instr(opcode.JUMP(finally_label, None))
		else:
			self.ctx.instr(opcode.JUMP(end_label, None))
		#### END TRY BB ####


		#### EXCEPT BB ####
		# NOTE: The except bb has no explicit entry, but is only jumped to by failures that 
		#		occur in SETUP_EXCEPT/END_EXCEPT
		self.ctx.prepare_label(except_label)

		# store aside the error state
		exc = (self.tmpname(), self.tmpname(), self.tmpname())
		self.ctx.instr(opcode.SETUP_EXCEPTION_HANDLER(exc, None))

		# prepare labels for all matcher and handler positions
		match_labels = [self.labelname('exm') for _ in node.handlers]
		handle_labels = [self.labelname('exh') for _ in node.handlers]

		# jump to the first matcher
		self.ctx.instr(opcode.JUMP(match_labels[0], None))

		# perform matching against the exception class, branching to the real handler blocks
		for i, handler in enumerate(node.handlers):
			if i + 1 < len(node.handlers):
				next_matcher = match_labels[i + 1]
			else:
				next_matcher = fail_label

			self.ctx.prepare_label(match_labels[i])
			if not handler.type: # generic handler
				self.ctx.instr(opcode.JUMP(handle_labels[i], None))
			elif isinstance(handler.type, py.Tuple):
				raise NotImplementedError
			elif isinstance(handler.type, (py.Name, py.Attribute, py.Subscript)):
				inst = self.visit(handler.type)
				matches = self.tmpname()
				matches.add_type(CIntegerType())
				matches.no_cleanup = True
				self.ctx.instr(opcode.COMPARE_EXCEPTION_MATCH(matches, exc[0], inst, handler))
				self.ctx.instr(opcode.BRANCH(matches, handle_labels[i], next_matcher, handler))

		##  #### FAILURE BB ####
		# for when we raise, but can't match an exception
		self.ctx.prepare_label(fail_label)
		self.ctx.instr(opcode.RESTORE_EXCEPTION(exc, None))
		self.ctx.instr(opcode.JUMP('end', None))
		##  #### END FAILURE BB ####

		# emit actual handler blocks
		for i, handler in enumerate(node.handlers):
			self.ctx.prepare_label(handle_labels[i])
			# load exception into name
			if handler.name:
				self._store_any(handler.name, exc[0])
			# visit actual block
			self.visit_nodelist(handler.body)
			# if we reach the end of the handler, jump out to finish or finally
			if node.finallybody:
				self.ctx.instr(opcode.JUMP(finally_label, None))
			else:
				self.ctx.instr(opcode.JUMP(end_label, None))
		#### END EXCEPT BB ####


		#### ORELSE BB ####
		self.ctx.prepare_label(orelse_label)

		# visit the orelse block
		self.visit_nodelist(node.orelse)

		# exit to finally (if we have one) or the end otherwise
		if node.finallybody:
			self.ctx.instr(opcode.JUMP(finally_label, None))
		else:
			self.ctx.instr(opcode.JUMP(end_label, None))
		#### END ORELSE BB ####


		#### FINALLY BB ####
		if node.finallybody:
			self.ctx.prepare_label(finally_label)
			self.visit_nodelist(node.finallybody)
			#self.ctx.instr(opcode.JUMP(end_label, None))
		#### END FINALLY BB ####

		# next block needs to take over where we leave off
		self.ctx.prepare_label(end_label)

		if node.finallybody:
			self.ctx.instr(opcode.END_FINALLY(finally_label, None))

	def visit_Raise(self, node):
		if not node.exc:
			self.ctx.instr(opcode.RERAISE(node))
		else:
			exc = self.visit(node.exc)
			exc.no_cleanup = True
			self.ctx.instr(opcode.RAISE(exc, node))


	### INDEX
	def visit_Index(self, node):
		return self.visit(node.value)


	def visit_Slice(self, node):
		raise SystemError("Found a naked slice!")


	### NAME ACCESS
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


	def visit_Subscript(self, node):
		if node.ctx in (py.Load, py.Aug):
			return self._load_any(node)
		else:
			raise NotImplementedError


	### FLOW
	def visit_Break(self, node):
		raise NotImplementedError("break")
	def visit_Continue(self, node):
		raise NotImplementedError("break")


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
	def visit_Dict(self, node):
		assert not node.keys or len(node.keys) == len(node.values)
		srcs = []
		if node.keys:
			for k, v in zip(node.keys, node.values):
				srcs.append(self.visit(k))
				srcs.append(self.visit(v))
		tgt = self.tmpname()
		self.ctx.instr(opcode.BUILD_DICT(tgt, *(srcs + [node])))
		return tgt


	def visit_Set(self, node):
		srcs = [self.visit(e) for e in node.elts] if node.elts else []
		tgt = self.tmpname()
		self.ctx.instr(opcode.BUILD_SET(tgt, *(srcs + [node])))
		return tgt


	def visit_List(self, node):
		srcs = [self.visit(e) for e in node.elts] if node.elts else []
		tgt = self.tmpname()
		self.ctx.instr(opcode.BUILD_LIST(tgt, *(srcs + [node])))
		return tgt


	def visit_Tuple(self, node):
		srcs = [self.visit(e) for e in node.elts] if node.elts else []
		tgt = self.tmpname()
		self.ctx.instr(opcode.BUILD_TUPLE(tgt, *(srcs + [node])))
		return tgt


	#### CONSTANTS
	def visit_Num(self, node):
		tgt = self.tmpname()
		self.ctx.instr(opcode.LOAD_CONST(tgt, node.n, node))
		return tgt

	def visit_Str(self, node):
		tgt = self.tmpname()
		self.ctx.instr(opcode.LOAD_CONST(tgt, PyStringType.dequote(node.s), node))
		return tgt
