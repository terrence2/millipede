'''
Check that class initializers are sane.
'''
__author__ = 'Terrence Cole <terrence@zettabytestorage.com>'

from millipede.lint.messages import E0100, E0101

MESSAGES = {E0100, E0101}

def analyse(unit):
	for classblock in unit.bst.all_classes:
		for block in classblock.methods:
			if block.ast.name.id == '__init__':
				for rv_node in block.returns:
					if rv_node.value is not None:
						yield E0101(rv_node.value)
				if len(block.yields) > 0:
					yield E0100(block.ast)

