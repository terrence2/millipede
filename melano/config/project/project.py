'''
Stores all per-project variables, or passes through to the parent project.
'''
__author__ = 'Terrence Cole <terrence@zettabytestorage.com>'

from melano.code.unit import MelanoCodeUnit
from configparser import ConfigParser
import os.path


class NoProjectError(Exception): pass
class ProjectCorruptError(Exception): pass


class MelanoProject:
	def __init__(self, config, name:str):
		self.config = config
		self.name = name

		self.project_dir = os.path.join(self.config.projects_dir, self.name)
		
		self.base_dir = None
		self.run_dir = None
		self.units = {}
		self.lint_masks = set()

		self.thaw()


	def lint_message_is_masked(self, name:str):
		return name in self.lint_masks


	def freeze(self):
		pass


	def thaw(self):
		if not os.path.isdir(self.project_dir):
			raise NoProjectError(self.name)

		parser = ConfigParser()
		parsed = parser.read([os.path.join(self.project_dir, 'config.ini')])
		if not parsed:
			raise ProjectCorruptError("Failed to read config for {}".format(self.name))
		
		# base project directory
		self.base_dir = parser.get('project', 'base_dir')
		if not os.path.exists(self.base_dir):
			raise ProjectCorruptError("No base directory for project {} at: {}".format(self.name, basedir))

		# logical run directory
		self.run_dir = parser.get('project', 'run_dir')
		if self.run_dir.startswith('/'):
			self.run_dir = os.path.realpath(self.run_dir)
		self.run_dir = os.path.realpath(os.path.join(self.base_dir, self.run_dir))

		# source directories
		srcdirs = []
		srcdirs_str = parser.get('project', 'src_dirs')
		for srcdir in srcdirs_str.split('\n'):
			srcdir.strip()
			if not srcdir.startswith('/'):
				srcdir = os.path.join(self.base_dir, srcdir)
			srcdir = os.path.realpath(srcdir)
			srcdirs.append(srcdir)
		
		# units
		for srcdir in srcdirs:
			for root, dirs, files in os.walk(srcdir):
				for filename in files:
					if filename.endswith('.py'):
						src = os.path.join(root, filename)
						assert src.startswith(self.run_dir), '{} not subdir of {}'.format(src, self.run_dir)
						src_modname = src[len(self.run_dir) + 1:].replace('/', '.')
						unit = MelanoCodeUnit(self.config, src)
						self.units[src_modname] = unit

		# lint message masking
		for name, value in parser.items('lint'):
			val = value.lower()
			if val == 'off' or val == 'no' or val == '0':
				self.lint_masks.add(name.upper())

