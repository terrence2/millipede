'''
Copyright (c) 2011, Terrence Cole.
All rights reserved.
'''
import millipede.ir.opcodes as opcode


class BasicBlock:
	def __init__(self, name, label, frame, ast):
		super().__init__()

		# globally unique name for this block
		self.name = name # str; globally unique

		# the frame local label that represents jumps to this block
		self.label = label # str

		# the frame and the frame's ast
		# FIXME: maybe this should be the ast node of the nearest controlling block
		self.frame = frame
		self.ast = ast

		# the set of instructions in this block
		self._instructions = None # [Op]

		# set of nodes that this block links to
		self.outbound = set()

		# set of nodes linking to this block
		self.inbound = set()


	def get_outbound_block_by_label(self, label:str):
		for bb in self.outbound:
			if bb.label == label:
				return bb
		raise KeyError("No such label: " + label)


	def disassemble(self):
		ib = ', '.join([bb.name for bb in self.inbound])
		ob = ', '.join([bb.name for bb in self.outbound])
		print('{} ({}) >>> ({})'.format(self.name, ib, ob))
		for op in self._instructions:
			try:
				print(op.format())
			except TypeError:
				raise SystemError('Failed to disassemble at op: {}'.format(op))
		print()



class BuiltinBlock(BasicBlock):
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self._instructions = [opcode.NOP(None)]


class OpaqueBlock(BuiltinBlock):
	def __init__(self):
		super().__init__('__opaque__', '__opaque__', None)
		self._instructions = []
		self.name = '__opaque__'
