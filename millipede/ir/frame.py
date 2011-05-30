'''
Copyright (c) 2011, Terrence Cole.
All rights reserved.
'''

class _MpFrame:
	def __init__(self, name):
		# the name of the frame -- should be globally unique
		self.name = name

		# the linear instructions for this frame
		self._instructions = []

		# set to a name when we want to add a label to the next instruction
		self._ready_label = None


	def prepare_label(self, name):
		'''Prepare a label to be placed on the next instruction.'''
		assert self._ready_label is None, "Attempted to ready 2 labels for the next statement: {} <- {}".format(self._ready_label, name)
		self._ready_label = name


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
