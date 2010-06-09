'''
Check that method arguments do not violate naming conventions.
'''
__author__ = 'Terrence Cole <terrence@zettabytestorage.com>'

from melano.lint.messages import C0201, E0201, C0202, E0202, C0203

MESSAGES = {C0201, E0201, C0202, E0202, C0203}

def analyse(unit):
	for block in unit.bst.all_methods:
		is_static = is_cls = False
		if block.ast.decorator_list:
			for deco in block.ast.decorator_list:
				if str(deco) == 'staticmethod': is_static = True
				elif str(deco) == 'classmethod': is_cls = True
		if str(block.ast.name) == '__new__':
			is_cls = True

		if not is_static and not is_cls:
			if not block.ast.args.args or len(block.ast.args.args) == 0:
				yield E0201(block.ast)
			elif block.ast.args.args[0].arg.id != 'self':
				yield C0201(block.ast.args.args[0])

		elif is_cls:
			if not block.ast.args.args or len(block.ast.args.args) == 0:
				yield E0202(block.ast)
			elif block.ast.args.args[0].arg.id != 'cls':
				yield C0202(block.ast.args.args[0])

		elif is_static:
			if block.ast.args.args and len(block.ast.args.args) > 0:
				firstname = block.ast.args.args[0].arg.id
				if firstname == 'self' or firstname == 'cls':
					yield C0203(block.ast.args.args[0])

