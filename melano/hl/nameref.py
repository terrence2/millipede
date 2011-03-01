'''
Copyright (c) 2011, Terrence Cole.
All rights reserved.
'''
from melano.hl.name import Name
import logging


class NameRef:
	def __init__(self, ref:Name):
		self.ref = ref
		self.inst = None

		# property flags
		self.is_global = False
		self.is_nonlocal = False


	def create_instance(self, name:str):
		'''
		Instance the type with a name.  Sets the new instance on the 'inst' variable.
		'''
		assert not self.inst
		self.inst = self.ref.get_type()(name)


	@property
	def name(self):
		return self.ref.name
	@name.setter
	def name(self, value):
		self.ref.name = value


	@property
	def ll(self):
		return self.ref.ll
	@ll.setter
	def ll(self, value):
		self.ref.ll = value


	@property
	def scope(self):
		return self.ref.scope
	@scope.setter
	def scope(self, value):
		self.ref.scope = value


	@property
	def parent(self):
		return self.ref.parent


	def get_type(self):
		return self.ref.get_type()

	def add_type(self, ty):
		self.ref.add_type(ty)


	def show(self, level):
		logging.info('{}Ref: {}'.format('\t' * level, self.ref.name))
