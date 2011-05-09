'''
Copyright (c) 2011, Terrence Cole.
All rights reserved.
'''

class EntityAttrAccess:
	def __init__(self, hlnode, ast):
		super().__init__()
		self.hlnode = hlnode
		self.ast = ast


class Entity:
	'''
	A 'thing' in the program that is usable in the standard ways.  E.g. attribute access, indexing, etc.
	'''
	def __init__(self):
		super().__init__()

		# The attribute map -- we record all potential attribute usage in the name
		self.attributes = {} # {str: HLType}

		# The subscript map -- we record all potential indexing of this name here
		self.subscripts = {} # {slice: HLType}


	def add_attribute(self, attrname, hlnode, ast):
		if attrname not in self.attributes:
			self.attributes[attrname] = []
		if hlnode:
			self.attributes[attrname].append(EntityAttrAccess(hlnode, ast))
			# If the name we are accessing the attribute on has a scope, then the reference needs to go
			#		on the scope as well, so that lookups on the scope can be aware of potential modifications to the scope.
			if hasattr(self, 'scope') and self.scope:
				self.scope.add_attribute(attrname, hlnode, ast)


	def add_subscript(self, slice, hltype):
		if slice not in self.subscripts:
			self.subscripts[slice] = []
		if hltype:
			self.subscripts[slice].append(hltype)


	def lookup_attribute(self, attrname):
		return self.attributes[attrname]

