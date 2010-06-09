'''
Check that method arguments do not violate naming conventions.
'''
__author__ = 'Terrence Cole <terrence@zettabytestorage.com>'

from melano.lint.messages import C0201, E0201, C0202, E0202, C0203, C0204, E0204

MESSAGES = {C0201, E0201, C0202, E0202, C0203, C0204, E0204}

def analyse(unit):
	for block in unit.bst.all_methods:
		ty = 'normal'
		if block.ast.decorator_list:
			for deco in block.ast.decorator_list:
				if str(deco) == 'staticmethod': ty = 'static'
				elif str(deco) == 'classmethod': ty = 'class'
		if str(block.ast.name) == '__new__':
			ty = 'class'
		if str(block.ast.name) == '__prepare__':
			#FIXME: technically we should also check if the class derives from type
			ty = 'metaclass'

		if ty == 'normal':
			if not block.ast.args.args or len(block.ast.args.args) == 0:
				yield E0201(block.ast)
			elif block.ast.args.args[0].arg.id != 'self':
				yield C0201(block.ast.args.args[0])

		elif ty == 'class':
			if not block.ast.args.args or len(block.ast.args.args) == 0:
				yield E0202(block.ast)
			elif block.ast.args.args[0].arg.id != 'cls':
				yield C0202(block.ast.args.args[0])

		elif ty == 'static':
			if block.ast.args.args and len(block.ast.args.args) > 0:
				firstname = block.ast.args.args[0].arg.id
				if firstname == 'self' or firstname == 'cls':
					yield C0203(block.ast.args.args[0])

		elif ty == 'metaclass':
			if not block.ast.args.args or len(block.ast.args.args) == 0:
				yield E0204(block.ast)
			elif block.ast.args.args[0].arg.id != 'mcs':
				yield C0204(block.ast.args.args[0])

