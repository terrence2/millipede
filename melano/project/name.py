'''
Copyright (c) 2011, Terrence Cole.
All rights reserved.
'''

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

		# TODO: this definitely needs some identifier translation, at least to remove unicode
		self.ll_name = self._as_lowlevel(name)

		# this name should be globally unique in all the project
		if parent and parent.owner:
			self.global_name = parent.owner.global_name + '_' + self.ll_name
		else:
			self.global_name = self.ll_name

		# a name can have a child scope (class/functions, etc)
		self.scope = None

	def _as_lowlevel(self, name):
		return name.replace('.', '_')

	def show(self, level):
		print('{}{:20}{:20}'.format('\t' * level, self.name, self.global_name))
		if self.scope:
			self.scope.show(level + 1)
