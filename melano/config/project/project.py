'''
Stores all per-project variables, or passes through to the parent project.
'''
__author__ = 'Terrence Cole <terrence@zettabytestorage.com>'

from melano.code.symbols.program import Program
from melano.code.unit import MelanoCodeUnit
from configparser import ConfigParser
import fnmatch
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

		self.db = Program(name)

		self.lint_masks = set() # name:str
		self.lint_option = {} # name:str -> str
		self.lint_filter = {} # name:str -> [path:str]

		self.thaw()


	def lint_message_is_masked(self, name:str) -> bool:
		return name.lower() in self.lint_masks


	def lint_file_is_masked(self, name:str, filename:str) -> bool:
		name = name.lower()
		if name not in self.lint_filter:
			return False
		proj_rel_filename = filename[len(self.base_dir) + 1:]
		path_globs = self.lint_filter[name]
		for path_glob in path_globs:
			if fnmatch.fnmatch(proj_rel_filename, path_glob):
				return True
		return False


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
			raise ProjectCorruptError("No base directory for project {} at: {}".format(self.name, self.base_dir))

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
						src_modname = src[len(self.run_dir) + 1:].replace('/', '.')[:-3]
						unit = MelanoCodeUnit(self.config, src)
						self.config.log.info("Found module: %s", src_modname)
						self.db.add_module(src_modname, unit)

		# lint message masking, filtering, and options
		for name, value in parser.items('lint'):
			if name.endswith('_option'):
				name = name[:-len('_option')]
				self.lint_option[name] = value

			elif name.endswith('_filter'):
				name = name[:-len('_filter')]
				self.lint_filter[name] = [v.strip() for v in value.split(';')]

			else:
				val = value.lower()
				if val == 'off' or val == 'no' or val == '0':
					self.lint_masks.add(name.upper())

