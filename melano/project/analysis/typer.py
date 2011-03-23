'''
Copyright (c) 2011, Terrence Cole.
All rights reserved.
'''
from melano.hl.coerce import Coerce
from melano.lang.visitor import ASTVisitor
from melano.py import ast as py
import logging
import pdb


class Typer(ASTVisitor):
	def __init__(self, project, module):
		self.project = project
		self.module = module


	def visit_Assign(self, node):
		self.visit(node.value)
		if not node.value.hl:
			logging.debug("Skipping typing through assignment because we did not propogate a hl node!")
			return
		for target in node.targets:
			self.visit(target)
			if isinstance(target, py.Attribute):
				target.attr.hl.add_type(node.value.hl.get_type())
				#logging.error("Skipping typing of attribute assignment")
			elif isinstance(target, py.Subscript):
				logging.error("Skipping typing of subscript assignment")
			elif isinstance(target, py.Name):
				target.hl.add_type(node.value.hl.get_type())
			elif isinstance(target, py.Tuple):
				for elt in target.elts:
					logging.error("Skipping typing of destructuring assignment to {}".format(str(elt)))
			else:
				raise NotImplementedError("Assignment to unknown node class in typer")
		#node.hl = Coerce(Coerce.OVERRIDE, *([t.hl for t in node.targets] + [node.value]))


	def visit_AugAssign(self, node):
		self.visit(node.value)
		self.visit(node.target)
		node.target.hl.add_type(node.value.hl.get_type())
		node.hl = Coerce(Coerce.INPLACE, node.target.hl, node.value.hl)

	'''
	def visit_Call(self, node):
		#print(dir(node))
		#import pdb; pdb.set_trace()
		self.visit_nodelist(node.args)
		self.visit_nodelist(node.keywords)
		self.visit(node.starargs)
		self.visit(node.kwargs)
		self.visit(node.func)
		# Check parameter types against annotation types.
		# Annotate parameters (in callee) with type of args/annotations.
		# Note type of annotated return as the type of the call.
		node.hl = node.func.hl
	'''


	def visit_BinOp(self, node):
		self.visit(node.left)
		self.visit(node.right)
		node.hl = Coerce(Coerce.GENERALIZE, node.left.hl, node.right.hl)



