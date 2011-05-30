'''
Copyright (c) 2011, Terrence Cole.
All rights reserved.
'''
from contextlib import contextmanager
from millipede.hl.nodes.module import MpModule
from millipede.ir.frame import _MpFrame
from millipede.ir.opcodes import *
from millipede.lang.visitor import ASTVisitor
from millipede.py import ast as py
import collections
import itertools
import logging
import pdb





class Ast2Ir(ASTVisitor):
	'''Reduces one module into an IR representation.  Calling visit produces a table mapping names (functions, 
		class definitions, the module itself, etc.) to IR code that implements the given AST.'''
	def __init__(self, project):
		super().__init__()

		# a mapping from frame names to the frame structures themselves
		self.frames = {}

		# the current frame
		self.ctx = None

		# the current python scope
		self.py_scope = None

		# provides unique names for our internal variables
		self._tmpnum = itertools.count(0)
		self._labelnum = collections.Counter()


	@contextmanager
	def new_frame(self, name):
		frame = _MpFrame(name)
		self.frames[name] = frame
		prior, self.ctx = self.ctx, frame
		yield
		self.ctx = prior


	@contextmanager
	def set_python_scope(self, scope):
		prior, self.py_scope = self.py_scope, scope
		yield
		self.py_scope = prior


	def tmpname(self):
		while True:
			nm = '_tmp' + str(next(self._tmpnum))
			try:
				self.py_scope.lookup(nm)
			except KeyError:
				return nm


	def labelname(self, base):
		out = base + str(self._labelnum[base])
		self._labelnum[base] += 1
		return out


	def generic_visit(self, node):
		logging.warning('Skipping: ' + str(node))
		return super().generic_visit(node)


	def visit_Module(self, node):
		with self.new_frame(node.hl.owner.global_c_name), self.set_python_scope(node.hl):
			self.visit_nodelist(node.body)


	def _store_any(self, node, name):
		if isinstance(node, py.Name):
			if isinstance(node.hl.parent, MpModule):
				self.ctx.instr(STORE_GLOBAL(node.hl, name, node))
			else:
				self.ctx.instr(STORE_LOCAL(node.hl, name, node))

	def _load_any(self, node):
		tgt = self.tmpname()
		if isinstance(node, py.Name):
			name = self.py_scope.lookup(str(node))
			if isinstance(name.parent, MpModule):
				self.ctx.instr(LOAD_GLOBAL(tgt, node.hl, node))
			else:
				self.ctx.instr(LOAD_LOCAL(tgt, node.hl, node))
		return tgt


	def visit_Assign(self, node):
		nm = self.visit(node.value)
		for tgt in node.targets:
			self._store_any(tgt, nm)


	def visit_BinOp(self, node):
		lhs = self.visit(node.left)
		rhs = self.visit(node.right)
		tgt = self.tmpname()
		if node.op == py.BitOr: cls = BINARY_OR
		elif node.op == py.BitXor: cls = BINARY_XOR
		elif node.op == py.BitAnd: cls = BINARY_AND
		elif node.op == py.LShift: cls = BINARY_LSHIFT
		elif node.op == py.RShift: cls = BINARY_RSHIFT
		elif node.op == py.Add: cls = BINARY_ADD
		elif node.op == py.Sub: cls = BINARY_SUBTRACT
		elif node.op == py.Mult: cls = BINARY_MULTIPLY
		elif node.op == py.Div: cls = BINARY_TRUE_DIVIDE
		elif node.op == py.FloorDiv: cls = BINARY_FLOOR_DIVIDE
		elif node.op == py.Mod: cls = BINARY_MODULO
		elif node.op == py.Pow: cls = BINARY_POWER
		self.ctx.instr(cls(tgt, lhs, rhs, node))
		return tgt


	def visit_Call(self, node):
		func = self.visit(node.func)
		posargs = []; kwargs = {}
		for arg in node.args:
			posargs.append(self.visit(arg))
		rv = self.tmpname()
		self.ctx.instr(CALL_FUNCTION(rv, func, posargs, None, None, None, node))
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
		if node.orelse:
			label_false = self.labelname('ifelse')

		nm = self.visit(node.test)
		self.ctx.instr(BRANCH(nm, label_true, label_false, node))

		self.ctx.prepare_label(label_true)
		self.visit_nodelist(node.body)
		if node.orelse:
			self.ctx.prepare_label(label_false)
			self.visit_nodelist(node.orelse)


	def visit_Name(self, node):
		if node.ctx in (py.Load, py.Aug):
			return self._load_any(node)


	#### CONTAINERS
	#def visit_Tuple(self, node):
	#	srcs = [self.visit(e) for e in node.elts]
	#	tgt = self.tmpname()
	#	self.ctx.instr(BUILD_TUPLE(tgt, *(srcs + [node])))
	#	return tgt


	#### CONSTANTS
	def visit_Num(self, node):
		tgt = self.tmpname()
		self.ctx.instr(LOAD_CONST(tgt, node.n, node))
		return tgt

	def visit_Str(self, node):
		tgt = self.tmpname()
		self.ctx.instr(LOAD_CONST(tgt, node.s, node))
		return tgt
