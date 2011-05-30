'''
Copyright (c) 2011, Terrence Cole.
All rights reserved.
'''

class BasicBlock:
	def __init__(self):
		super().__init__()

		# globally unique name for this block
		self.name = None # str; globally unique

		# the frame local label that represents jumps to this block
		self.label = None # str

		# the set of instructions in this block
		self._instructions = None # [Op]

		# set of nodes that this block links to
		self.outbound = set()

		# set of nodes linking to this block
		self.inbound = set()

	def disassemble(self):
		print('>>> From: {}'.format(', '.join([bb.name for bb in self.inbound])))
		print('{}:'.format(self.name))
		for op in self._instructions:
			try:
				print(op.format())
			except TypeError:
				raise SystemError('Failed to disassemble at op: {}'.format(op))
		print('<<< To: {}'.format(', '.join([bb.name for bb in self.outbound])))



class BuiltinBlock(BasicBlock):
	def __init__(self):
		super().__init__()
		self._instructions = []


class OpaqueBlock(BuiltinBlock):
	def __init__(self):
		super().__init__()
		self._instructions = []
		self.name = '__opaque__'
