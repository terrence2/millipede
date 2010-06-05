'''
Check that return and yield are used sanely.
'''
__author__ = 'Terrence Cole <terrence@zettabytestorage.com>'

from melano.lint.messages import E0104, E0105

MESSAGES = {E0104, E0105}


def analyse(unit):
	for node in unit.bst.all_invalid:
		if node.__class__.__name__ == 'Return':
			yield E0104(node)
		elif node.__class__.__name__ == 'Yield':
			yield E0105(node)

