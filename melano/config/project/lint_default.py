'''
Specialize the MelanoProject to implement a hard-coded set of default values.
'''
__author__ = 'Terrence Cole <terrence@zettabytestorage.com>'

from melano.code.unit import MelanoCodeUnit
from .project import MelanoProject
import os


class LintDefaultProject(MelanoProject):
	'''Provide a good value for the project base-dir and units from what
		we can glean from the command line parsed by the config.'''

	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)

		# base and run are where we invoke from
		self.base_dir = os.getcwd()
		self.run_dir = self.base_dir

		# collect all filenames that were referenced on the command line	
		filenames = []
		for name in self.config.args:
			nodename = os.path.realpath(name)
			if os.path.isdir(nodename):
				for root, dirs, files in os.walk(nodename):
					for fname in files:
						if fname.endswith('.py'):
							filenames.append(os.path.join(root, fname))
			else:
				filenames.append(nodename)

		# build units for all referenced files
		for src in filenames:
			assert src.startswith(self.run_dir)
			src_modname = src[len(self.run_dir) + 1:].replace('/', '.')
			unit = MelanoCodeUnit(self.config, src)
			self.units[src_modname] = unit


	def freeze(self):
		pass

	def thaw(self):
		pass

