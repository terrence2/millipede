'''
Copyright (c) 2011, Terrence Cole.
All rights reserved.
'''
from melano.c.types.pyobject import PyObjectType


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

		# a name suitable for use in a c program
		# 		this gets used for the local identifier for a Name, when such is useful  
		self.ll_name = self._as_lowlevel(name)

		# this name should be globally unique among the project's modules/scopes
		#		this name is used for objects that need to be used globally (e.g. functions, modules)
		if parent and parent.owner:
			self.global_name = parent.owner.global_name + '_' + self.ll_name
		else:
			self.global_name = self.ll_name

		# a name can have a child scope (class/functions, etc)
		self.scope = None

		# the types that we have proven this name can take
		self.types = []

		# the ll instance
		self.ll_inst = None


	def get_type(self) -> type:
		'''
		Query the type list to find the most appropriate type for this name.
		'''
		assert len(self.types) <= 1
		if len(self.types):
			return self.types[0]
		return PyObjectType


	def create_instance(self, name:str):
		'''
		Instance the type with a name.  Sets the new instance on the 'inst' variable.
		'''
		self.inst = self.get_type()(name)


	def _as_lowlevel(self, name):
		return name.replace('.', '_')


	def show(self, level):
		print('{}{:20}{:20}'.format('\t' * level, self.name, self.global_name))
		if self.scope:
			self.scope.show(level + 1)
