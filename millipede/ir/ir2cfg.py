'''
Copyright (c) 2011, Terrence Cole.
All rights reserved.
'''
from millipede.hl.nodes.builtins import Builtins
from millipede.ir.basicblock import OpaqueBlock, BasicBlock
from millipede.ir.frame import _MpFrame
from millipede.ir.opcodes import BRANCH, JUMP, CALL_FUNCTION
import itertools
import pdb




def ir_2_cfg(frames:{str:_MpFrame}):
	blocks = {} # global set of blocks, indexed by unique name
	for name, frame in frames.items():
		blocks.update(_frame_2_local_cfg(frame))

	# link all external calls
	blocks['__opaque__'] = OpaqueBlock()
	for block in blocks.values():
		for op in block._instructions:
			if isinstance(op, CALL_FUNCTION):
				tgt_owner_scope = op.ast.func.hl.deref().parent
				if isinstance(tgt_owner_scope, Builtins):
					block.outbound.add(blocks['__opaque__'])
					print("TODO: fill in opaque nodes where needed")

	# show all blocks
	for block in blocks.values():
		block.disassemble()


def _find_end(ops, pos):
	"Find the next branch or labeled entry point."
	while True:
		if pos >= len(ops):
			return len(ops) - 1
		if isinstance(ops[pos], (BRANCH, JUMP, CALL_FUNCTION)):
			return pos + 1
		if ops[pos].label:
			return pos
		pos += 1

def _find_start(ops, pos):
	"Find the next label."
	while True:
		if pos >= len(ops):
			return len(ops) - 1
		if ops[pos].label:
			return pos
		pos += 1

def _decompose_blocks(frame):
	unique = itertools.count(1)

	bb = BasicBlock()
	bb.label = 'start'
	blocks = {bb.label: bb}
	bb.name = frame.name
	s = 0
	while True:
		e = _find_end(frame._instructions, s + 1)
		bb._instructions = frame._instructions[s:e]
		bb._instructions[0].ast.bb = bb

		# find start at next label; instructions after a jump without a branch label are unreachable
		# Note: we may have instructions, e.g. after a return.. so even if our prior jump wasn't at
		#		the block end, we may still be at the last bb.  We span to the next start before checking
		#		so that we don't end up with a zero-length bb at the end.
		s = _find_start(frame._instructions, e)

		# if we have reached the end
		if s == len(frame._instructions) - 1:
			break

		# craft next basicblock
		bb = BasicBlock()
		bb.name = frame.name + str(next(unique))
		bb.label = frame._instructions[s].label
		blocks[bb.label] = bb

	return blocks

def _add_link(blocks, bb, tgt_label):
	'''Given a map of labels to blocks, a specific block, and a target label for the link, link the block to the
		block at the label.'''
	tgt_block = blocks[tgt_label]
	bb.outbound.add(tgt_block)
	tgt_block.inbound.add(bb)

def _link_blocks_internal(blocks):
	'''Find branches internal to the frame and link them together.'''
	for bb in blocks.values():
		branch = bb._instructions[-1]
		if isinstance(branch, JUMP):
			_add_link(blocks, bb, branch.label_target)
		elif isinstance(branch, BRANCH):
			_add_link(blocks, bb, branch.label_true)
			_add_link(blocks, bb, branch.label_false)


def _frame_2_local_cfg(frame):
	'''Build a frame-local cfg for the given frame.  Return the blocks from the frame, indexed by name.'''
	blocks = _decompose_blocks(frame)
	_link_blocks_internal(blocks)
	return {bb.name: bb for bb in blocks.values()}

