'''
Copyright (c) 2011, Terrence Cole.
All rights reserved.
'''
from millipede.hl.types.pyfunction import PyFunctionType
from millipede.ir.opcodes import IMPORT_NAME
import pdb


class CFGVisitor:
	def __init__(self, V, E):
		super().__init__()
		self.V = V
		self.E = E

		# the current block we are in
		self.block = None


	def visit_Block(self, block):
		self.block = block
		for op in block._instructions[:-1]:
			self.visit_Op(op)
		op = block._instruction[-1]

		'''
		### External Linkage
		if type(op) == opcode.IMPORT_NAME:
			pass
		### Internal Linkage
		elif type(op) == opcode.BRANCH:
			pass
		elif type(op) == opcode.JUMP:
			pass
		else:
			raise NotImplementedError("Unknown branch type: " + str(type(op)))
		return block
		'''


	def visit_Op(self, op):
		fn = getattr(self, 'visit_' + type(op).__name__, self.visit_Op_generic)
		fn(op)


	def visit_Op_generic(self, op):
		print("MISSING OP: {}".format(str(op)))



class VirtualInterpret(CFGVisitor):
	#### EXTERNAL BRANCHES
	def visit_IMPORT_NAME(self, op):
		# FIXME: is this too simple?
		name = op.ast.hl
		tgt_frame = name.scope
		self.visit_Block(tgt_frame.get_head_block())

		# update intermediate
		op.target.add_type(tgt_frame.get_type())


	#### OPS
	def visit_MAKE_FUNCTION(self, op):
		op.target.add_type(PyFunctionType(op.operands[0]))

	def visit_STORE_GLOBAL(self, op):
		op.target.add_type(op.operands[0].get_type())

	def visit_NOP(self, op): pass
