'''
Copyright (c) 2011, Terrence Cole.
All rights reserved.
'''
from melano.hl.types.hltype import HLType
from melano.hl.types.pyobject import PyObjectType
import logging


class Name:
	'''
	An item that can be placed in a symbol table.  Contains information about a named
	python entity, possibly including another symbol table.
	'''
	def __init__(self, name:str, parent):
		'''
		parent: Scope (we cannot formally declare this type because Scope needs Name)
		'''
		self.name = name
		self.parent = parent

		# a name can have a child scope (class/functions, etc)
		self.scope = None

		# the types that we have proven this name can take
		self.types = []

		# the ll instance
		self.ll = None


	@property
	def global_name(self):
		if self.parent and self.parent.owner:
			return self.parent.owner.global_name + '.' + self.name
		return self.name


	def get_type(self) -> type:
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
		base = self.types[0]
		for ty in self.types[1:]:
			if base == ty:
				continue
			base = base.common_base_type(ty.__class__)

		#print("RET: {} for {} types".format(base, self.types))
		return base


	def add_type(self, ty:HLType):
		self.types.append(ty)


	def _as_lowlevel(self, name):
		return name.replace('.', '_').replace('<', '_').replace('>', '_')


	def show(self, level):
		if self.scope:
			self.scope.show(level + 1)
		else:
			logging.info('{}Name: {}'.format('\t' * level, self.name))
		#print('{}{:20}{:20}'.format('\t' * level, self.name, self.global_name))
		#if self.scope:
		#	self.scope.show(level + 1)