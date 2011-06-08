'''
Copyright (c) 2011, Terrence Cole.
All rights reserved.
'''
from collections import OrderedDict
from millipede.hl.nodes.name import Name
from millipede.hl.nodes.nameref import NameRef
from millipede.hl.types.pydict import PyDictType
from millipede.ir.basicblock import BasicBlock
from millipede.lang.ast import AST
import itertools
import logging


class Scope:
	'''
	Acts as a symbol table in the HL tree, a list of instructions in the half compiled tree, and a list of blocks when we
		are in cfg form.  This may be referred to as a Frame when we are using it as a container of instructions/blocks.  
	'''
	def __init__(self, owner:Name, *args, **kwargs):
		super().__init__(*args, **kwargs)

		# the name that owns this scope, in the owning scope
		self.owner = owner

		# the symbols defined in this block
		self.symbols = OrderedDict()

		# Keep track of how many labels we have used per prefix, so that we can
		#		ensure that each label we create is unique.
		self._labels = {}

		# Temporarily hold instructions in LinearIR until we can dump them into basic blocks for CFG form.
		self._instructions = []

		# A temp slot where we prepare a name to be set on the next instruction when compiling to LinearIR.
		self._ready_label = None

		# After we are in CFG form, hold the linear list of basic blocks that we are composed from.  Also, find
		#		and record all exit points from this frame.
		self._blocks = []
		self._block_tails = []


	def lookup(self, name:str) -> Name:
		raise NotImplementedError("Every Scope type needs its own lookup routines.")


	def get_next_scope(self):
		'''
		Return the next highest scope to look in for names.
		Note: use this instead of owner.parent to skip class scopes.
		'''
		cur = self.owner.parent
		from millipede.hl.nodes.class_ import MpClass
		while isinstance(cur, MpClass):
			cur = cur.owner.parent
		return cur


	def has_name(self, name:str) -> bool:
		return name in self.symbols


	def owns_name(self, name:str) -> bool:
		return name in self.ownership


	def set_needs_closure(self):
		'''Scopes that might need a closure add a flag here, scopes that a closure cannot be contained, e.g.
			the module, block further propagation.'''
		if self.owner.parent:
			self.owner.parent.set_needs_closure()


	def get_label(self, prefix):
		if prefix not in self._labels:
			self._labels[prefix] = itertools.count()
		return prefix + str(next(self._labels[prefix]))


	def add_symbol(self, name:str, init:object=None, ast:AST=None):
		if not init:
			init = Name(name, self, ast)
		self.symbols[name] = init
		return self.symbols[name]


	def set_reference(self, sym:Name):
		'''Add a reference to an existing name.  Like add reference, except that this ensures
			that the captured name _is_ a reference.  We use this when we know we are not
			the owner, but may be marked as the owner.  E.g. non-local definition before the
			symbol was created, etc.'''
		if sym.name in self.symbols and isinstance(self.symbols[sym.name], NameRef):
			return self.symbols[sym.name]
		self.symbols[sym.name] = NameRef(sym)
		return self.symbols[sym.name]



	def show(self, level=0):
		for sym in self.symbols.values():
			sym.show(level + 1)


	#######
	# Frame related
	def prepare_label(self, name):
		'''Prepare a label to be placed on the next instruction.'''
		assert self._ready_label is None, "Attempted to ready 2 labels for the next statement: {} <- {}".format(self._ready_label, name)
		self._ready_label = name


	def label_instr(self, label, op):
		assert self._ready_label is None, "Attempted to label instr with prepared label set: {} <- {}".format(self._ready_label, label)
		op.label = label
		self._instructions.append(op)


	def instr(self, op):
		'''Add an instruction to this frame.'''
		self._instructions.append(op)

		# if we have a label readied, put it on this op and clear
		if self._ready_label:
			self._instructions[-1].label = self._ready_label
			self._ready_label = None


	def disassemble(self):
		for op in self._instructions:
			try:
				print(op.format())
			except TypeError:
				raise SystemError('Failed to disassemble at op: {}'.format(op))


	def set_blocks(self, blocks:[BasicBlock]):
		'''Gets the list of created blocks, in-order, after we break them up from our instructions for use in the cfg.
		This will generally get overridden to find and set the block tails.
		'''
		self._blocks = blocks

	def get_head_block(self):
		'''The head block is always the first block in the frame.'''
		return self._blocks[0]

	def get_tail_blocks(self):
		'''Tail blocks should be collected when we first set the blocks and will depend on the frame's type.'''
		return self._block_tails
