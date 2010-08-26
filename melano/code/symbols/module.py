'''
Top-level names from a python file.  These can be classes, function, or symbols.
'''
__author__ = 'Terrence Cole <terrence@zettabytestorage.com>'

from .block import Block



class Module(Block):
	'''The toplevel block of a python file.'''
	def __init__(self, name, unit, *args, **kwargs):
		super().__init__(name, None, *args, **kwargs)
		self.unit = unit


	def get_filename(self):
		return self.unit.filename


	def get_node(self):
		if not self.node:
			self.node = self.unit.ast

			from .visit_names import NameExtractor
			from .visit_types import TypeExtractor

			# parse the unit to populate the module
			names = NameExtractor(self)
			names.visit(self.unit.ast)

			# parse the unit to populate the module
			types = TypeExtractor(self)
			types.visit(self.unit.ast)


		return super().get_node()

