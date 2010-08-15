'''
The top-level program symbol type.  Contains modules and packages.
'''
__author__ = 'Terrence Cole <terrence@zettabytestorage.com>'

from .visit_names import NameExtractor
from .visit_types import TypeExtractor
from .namespace import Namespace
from .package import Package
from .module import Module


class Program(Namespace):
	'''A collection of packages.'''

	def add_module(self, modname:str, unit):
		'''Add a dotted name to this symbol database, splitting into package.'''
		parts = modname.split('.')
		packages = parts[:-1]
		module = parts[-1]

		# create packages for all levels up to module
		pkg = self
		for p in packages:
			if p not in pkg.symbols:
				pkg.symbols[p] = Package(p)
			pkg = pkg.symbols[p]

		# add the module
		pkg.symbols[module] = Module(module, unit.ast)

		# parse the unit to populate the module
		names = NameExtractor(pkg.symbols[module])
		names.visit(unit.ast)

		# parse the unit to populate the module
		types = TypeExtractor(pkg.symbols[module])
		types.visit(unit.ast)


