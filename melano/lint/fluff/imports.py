'''
Check that import statments are sane.
'''
__author__ = 'Terrence Cole <terrence@zettabytestorage.com>'

from melano.lint.messages import W0401, W0410

MESSAGES = {W0401, W0410}

def analyse(unit):
	for node in unit.bst.futures + unit.bst.all_imports:
		# NOTE: import * is a parse error, so this is ImportFrom
		for alias in node.names:
			if str(alias.name) == '*':
				yield W0401(node, None, node.module)
		
	for node in unit.bst.all_imports:
		if hasattr(node, 'module') and str(node.module) == '__future__':
			yield W0410(node)

