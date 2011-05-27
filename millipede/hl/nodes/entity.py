'''
Copyright (c) 2011, Terrence Cole.
All rights reserved.
'''
from millipede.hl.types.hltype import HLType
from millipede.hl.types.pyobject import PyObjectType

class EntityAttrAccess:
	def __init__(self, hlnode, ast):
		super().__init__()
		self.hlnode = hlnode
		self.ast = ast


class Entity:
	'''
	A 'thing' in the program that is usable in the standard ways.  E.g. attribute access, indexing, etc.
	'''
	def __init__(self, ast):
		super().__init__()

		# The attribute map -- we record all potential attribute usage in the name
		self.attributes = {} # {str: HLType}

		# The subscript map -- we record all potential indexing of this name here
		self.subscripts = {} # {slice: HLType}

		# the types that we have proven this name can take
		self.types = []

		# the ll instance
		self.ll = None

		# a ref to the ast where this name is defined
		self.ast = ast


	def get_display_name(self):
		return 'unimplemented'


	def add_attribute(self, attrname, hlnode, ast):
		if attrname not in self.attributes:
			self.attributes[attrname] = []
		if hlnode:
			self.attributes[attrname].append(EntityAttrAccess(hlnode, ast))
			# If the name we are accessing the attribute on has a scope, then the reference needs to go
			#		on the scope as well, so that lookups on the scope can be aware of potential modifications to the scope.
			if hasattr(self, 'scope') and self.scope:
				self.scope.add_attribute(attrname, hlnode, ast)


	def lookup_attribute(self, attrname):
		return self.attributes[attrname]


	def add_subscript(self, slice, hltype):
		if slice not in self.subscripts:
			self.subscripts[slice] = []
		if hltype:
			self.subscripts[slice].append(hltype)


	def add_type(self, ty:HLType):
		self.types.append(ty)


	def get_type(self):
		'''
		Query the type list to find the most appropriate type for this name.
		'''
		# if we have only one type assigned, just use it
		if len(self.types) == 1:
			return self.types[0]
		# if we have no types, then we just use the most generic possible type
		if not len(self.types):
			return PyObjectType()

		# otherwise, we have to find a common base
		base = PyObjectType.common_base(self.types)

		#print("RET: {} for {} types".format(base, self.types))
		return base()


	def get_type_list(self):
		'''
		Return all types attached to this node.
		'''
		if self.types:
			return self.types
		return [PyObjectType()]
