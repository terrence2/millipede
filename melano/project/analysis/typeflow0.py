'''
Copyright (c) 2011, Terrence Cole.
All rights reserved.
'''
from melano.hl.nodes.attribute import Attribute
from melano.hl.nodes.call import Call
from melano.hl.nodes.coerce import Coerce
from melano.hl.nodes.entity import Entity
from melano.hl.nodes.subscript import Subscript
from melano.lang.visitor import ASTVisitor
from melano.py import ast as py
import logging
import pdb


class TypeFlow0(ASTVisitor):
	def __init__(self, project, module):
		super().__init__()
		self.project = project
		self.module = module


	def visit_Attribute(self, node):
		self.visit(node.value)
		node.hl = Attribute(node.value, str(node.attr), node)


	def visit_Assign(self, node):
		self.visit(node.value)
		self.visit_nodelist(node.targets)
		node.hl = Coerce(Coerce.OVERRIDE, *([t.hl for t in node.targets] + [node.value.hl]))


	def visit_AugAssign(self, node):
		self.visit(node.value)
		self.visit(node.target)
		node.hl = Coerce(Coerce.INPLACE, node, node.target.hl, node.value.hl)


	def visit_BinOp(self, node):
		self.visit(node.left)
		self.visit(node.right)
		node.hl = Coerce(Coerce.GENERALIZE, node, node.left.hl, node.right.hl)


	def visit_BoolOp(self, node):
		self.visit_nodelist(node.values)
		node.hl = Coerce(Coerce.BOOLEAN, node, [v.hl for v in node.values])


	def visit_Call(self, node):
		self.visit(node.func)
		self.visit_nodelist(node.args)
		self.visit_nodelist(node.keywords)
		self.visit(node.starargs)
		self.visit(node.kwargs)
		node.hl = Call(node.func.hl, node)


	def visit_IfExp(self, node):
		self.visit(node.test)
		self.visit(node.body)
		self.visit(node.orelse)
		node.hl = Entity(node)


	def visit_Subscript(self, node):
		# Note: references through the lhs of a subscript are always a ref, not a name, so we need to do
		#		attribute value updates in linking
		self.visit(node.value)
		self.visit(node.slice)
		node.hl = Subscript(node.value.hl, node.slice, node)


	def visit_Tuple(self, node):
		self.visit_nodelist(node.elts)
		#for i, e in enumerate(node.elts):
		#	node.hl.add_subscript(i, e.get_type())


	def visit_UnaryOp(self, node):
		self.visit(node.operand)
		if node.op == py.Not:
			node.hl = Coerce(Coerce.BOOLEAN, node, node.operand.hl)
		else:
			node.hl = Coerce(Coerce.INPLACE, node, node.operand.hl)

