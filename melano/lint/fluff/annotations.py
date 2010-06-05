'''
Check that method have annotations.
'''
__author__ = 'Terrence Cole <terrence@zettabytestorage.com>'

from melano.lint.messages import C0113, C0114

MESSAGES = {C0113, C0114}

def analyse(unit):
	for block in unit.bst.all_functions + unit.bst.all_methods:
		node = block.ast
		if node.args.args:
			arglist = node.args.args
			if block in unit.bst.all_methods:
				arglist = node.args.args[1:]
			for arg in arglist:
				if not arg.annotation:
					yield C0113(arg, node.name, arg.arg)

		if node.args.kwonlyargs:
			for arg in node.args.kwonlyargs:
				if not arg.annotation:
					yield C0113(arg, node.name, arg.arg)

		for rv_node in block.returns:
			if rv_node.value is not None and not node.returns:
				yield C0114(rv_node, node.name)


