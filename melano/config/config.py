'''
Load, track, and store the globally useful bits of the melano configuration.
'''
__author__ = 'Terrence Cole <terrence@zettabytestorage.com>'

import os
import os.path


class MelanoConfig:
	def __init__(self, basedir:str=''):
		'''Set default configuration.  Do a 'thaw' to restore from an existing
			configuration for the current user or given configuration 
			directory, if possible.'''
		
		# discover the config directory
		self.base_dir = basedir
		if not basedir:
			self.base_dir = os.path.join(os.path.expanduser('~'), 
						'.config', 'melinto')

		# build all configuration directories
		self.projects_dir = os.path.join(self.base_dir, 'projects')
		self.cache_dir = os.path.join(self.base_dir, 'cache')
		self.config_filename = os.path.join(self.base_dir, 'config.ini')

		# ensure all required directories exist
		if not os.path.exists(self.base_dir):
			os.makedirs(self.base_dir, 0o755)
		if not os.path.exists(self.projects_dir):
			os.makedirs(self.projects_dir, 0o755)
		if not os.path.exists(self.cache_dir):
			os.makedirs(self.cache_dir, 0o755)


	def thaw(self):
		raise NotImplementedError()
	
	def freeze(self):
		raise NotImplementedError()

