'''
Copyright (c) 2011, Terrence Cole.
All rights reserved.
'''
from millipede.hl.nodes.builtins import Builtins
from millipede.hl.nodes.scope import Scope
from millipede.ir.basicblock import OpaqueBlock, BasicBlock
import itertools
import logging
import millipede.ir.opcodes as opcode
import pdb



def ir_2_local_cfgs(frames:{str:Scope}):
	V = {} # global map of blocks, indexed by unique name
	E = set() # global set of edges
	for frame in frames.values():
		v, e = _frame_2_local_cfg(frame)
		V.update(v)
		E |= e

	# link all external calls
	#for frame in frames.values():
	#	for i, bb in enumerate(frame._blocks):
	#		next_bb = frame._blocks[i + 1] if i < len(frame._blocks) - 1 else None
	#		e = _link_external(bb, next_bb, V)
	#		E |= e

	#for block in V.values():
	#	e = _link_external(block, V)
	#	E |= e

	# show all blocks
	print("\Locally Linked Blocks:")
	for block in V.values():
		block.disassemble()

	return V, E


'''
def _link_external(block, next_block, V):
	e = set()
	def _lnk(a, b):
		a.outbound.add(b)
		b.inbound.add(a)
		e.add((a.name, b.name))

	for op in block._instructions:
		scope = None
		if isinstance(op, opcode.IMPORT_NAME):
			assert op is block._instructions[-1] and next_block is not None

			# follow the link our linker inserted to get to the module targeted by the import
			scope = op.operands[0].hl.scope
			assert scope


		elif isinstance(op, opcode.CALL_GENERIC):
			assert op is block._instructions[-1] and next_block is not None

			# follow the link our linker inserted to get to the function targeted by the call
			scope = op.ast.func.hl.deref().scope
			assert scope


		if scope:
			hd = scope.get_head_block()
			_lnk(block, hd)

			tails = scope.get_tail_blocks()
			assert tails
			for tail in tails:
				_lnk(tail, next_block)

	return e
'''

def _find_end(ops, pos):
	"Find the next branch or labeled entry point."
	while True:
		if pos >= len(ops) - 1:
			return len(ops) - 1
		if isinstance(ops[pos], (opcode.BRANCH, opcode.JUMP, opcode.CALL_GENERIC, opcode.RETURN_VALUE, opcode.IMPORT_NAME)):
			return pos
		#if ops[pos].label:
		#	return pos
		pos += 1

def _find_start(ops, pos):
	"Find the next label."
	while True:
		if pos >= len(ops) - 1:
			return len(ops) - 1
		if ops[pos].label:
			return pos
		pos += 1

def _decompose_blocks(frame):
	unique = itertools.count(1)

	bb = BasicBlock(frame.owner.global_c_name, 'start', frame, frame.ast)
	blocks = [bb]
	s = 0
	while True:
		e = _find_end(frame._instructions, s)
		bb._instructions = frame._instructions[s:e + 1]
		for op in bb._instructions:
			if op.ast:
				op.ast.bb = bb

		# find start at next label; instructions after a jump without a branch label are unreachable
		# Note: we may have instructions, e.g. after a return.. so even if our prior jump wasn't at
		#		the block end, we may still be at the last bb.  We span to the next start before checking
		#		so that we don't end up with a zero-length bb at the end.
		s = _find_start(frame._instructions, e + 1)

		# if we have reached the end
		if s == e:
			assert s == len(frame._instructions) - 1
			break

		# craft next basicblock
		bb = BasicBlock(frame.owner.global_c_name + str(next(unique)), frame._instructions[s].label, frame, frame.ast)
		blocks.append(bb)

	frame.set_blocks(blocks)
	return {bb.label: bb for bb in blocks}


def _add_link(blocks, bb, tgt_label, E):
	'''Given a map of labels to blocks, a specific block, and a target label for the link, link the block to the
		block at the label.'''
	tgt_block = blocks[tgt_label]
	bb.outbound.add(tgt_block)
	tgt_block.inbound.add(bb)
	E.add((bb.name, tgt_block.name))


def _link_blocks_internal(blocks):
	'''Find branches internal to the frame and link them together.'''
	E = set()
	for bb in blocks.values():
		branch = bb._instructions[-1]
		if isinstance(branch, opcode.JUMP):
			_add_link(blocks, bb, branch.label_target, E)
		elif isinstance(branch, opcode.BRANCH):
			_add_link(blocks, bb, branch.label_true, E)
			_add_link(blocks, bb, branch.label_false, E)
	return E


def _frame_2_local_cfg(frame):
	'''Build a frame-local cfg for the given frame.  Return the blocks from the frame, indexed by name.'''
	blocks = _decompose_blocks(frame)
	E = _link_blocks_internal(blocks)
	return {bb.name: bb for bb in blocks.values()}, E

