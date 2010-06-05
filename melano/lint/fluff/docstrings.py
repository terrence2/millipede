'''
Check that modules, classes, and functions have docstrings.
'''
__author__ = 'Terrence Cole <terrence@zettabytestorage.com>'

from melano.lint.message import C0111, C0112

MESSAGES = {C0111, C0112}


def analyse(unit):
	if unit.bst.docstring is None:
		yield C0111(unit.bst.ast)
	elif len(unit.bst.docstring) == 0:
		yield C0112(unit.bst.ast)

	for node in unit.bst.all_functions + unit.bst.all_methods:
		if node.docstring is None:
			yield C0111(node.ast, node.ast.name)
		elif len(node.docstring) == 0:
			yield C0112(node.ast, node.ast.name)

	for node in unit.bst.all_classes:
		if node.docstring is None:
			yield C0111(node.ast, node.ast.name)
		elif len(node.docstring) == 0:
			yield C0112(node.ast, node.ast.name)

