'''
Check that method have annotations.
'''
__author__ = 'Terrence Cole <terrence@zettabytestorage.com>'

from millipede.lint.messages import E0106

MESSAGES = {E0106}

def analyse(unit):
	for block in unit.bst.all_functions + unit.bst.all_methods:
		have_return_value = False
		for rv_node in block.returns:
			if rv_node.value:
				have_return_value = rv_node
		if have_return_value and len(block.yields) > 0:
			yield E0106(have_return_value, block.ast.name)

