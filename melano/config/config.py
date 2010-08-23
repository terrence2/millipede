'''
Load, track, and store the globally useful bits of the melano configuration.
'''
__author__ = 'Terrence Cole <terrence@zettabytestorage.com>'

from melano import VERSION
from melano.config.project.default import DefaultProject
from melano.config.project.project import MelanoProject
from melano.config.python_language import PythonLanguage
from melano.util.signal import Signal
import errno
import hashlib
import logging
import optparse
import os
import os.path
import sys



class MelanoConfig:
	def __init__(self, basedir:str='', mode:str='lint'):
		'''Set default configuration.  Do a 'thaw' to restore from an existing
			configuration for the current user or given configuration 
			directory, if possible.
			
			mode:str -- one of 'lint', 'compile', or 'ide'
		'''
		# global mode switch
		self.mode = mode

		# log target
		self.log = logging.getLogger("Melano")
		self.log.setLevel(logging.WARNING)
		self.log.addHandler(logging.StreamHandler(sys.stdout))

		# discover the config directory
		self.base_dir = basedir
		if not basedir:
			self.base_dir = os.path.join(os.path.expanduser('~'),
						'.config', 'melano')

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

		# find our application data
		self.data_dir = '/usr/share/melano-{}/'.format(VERSION)
		if os.path.exists('./data/grammar/python-3.1'):
			self.data_dir = os.path.join(os.path.realpath('.'), 'data')

		# track what we know about all interpreters that we support
		self.interpreters = {
			'3.1': PythonLanguage(self, '3.1')
		}

		# parse the commandline
		cliparse = optparse.OptionParser()
		cliparse.add_option('-p', '--project', default=None, dest="project",
					metavar="PROJECT", help="The project to load.")
		options, self.args = cliparse.parse_args()

		# the project option
		if options.project:
			self.project = MelanoProject(self, options.project)
		else:
			self.project = DefaultProject(self, self.mode + '-default')

		# signals
		self.projectChanged = Signal()


	def thaw(self):
		raise NotImplementedError()


	def freeze(self):
		raise NotImplementedError()


	def get_project_names(self):
		'''Return a list of all known projects.'''
		return os.listdir(self.projects_dir)


	def get_project(self):
		'''Return the currently loaded project.'''
		return self.project


	def set_project(self, project_name:str):
		'''Create an set a new project as the current active project.'''
		self.project = MelanoProject(self, project_name)
		self.projectChanged.emit(project_name)


	def get_cachefile(self, name:str):
		'''Build a cache location that is unique for name.'''
		tgt = hashlib.sha1(name.encode('UTF-8')).hexdigest()
		tgt0 = tgt[0:3]
		tgt1 = tgt[3:6]
		tgt2 = tgt[6:]

		cachedir = os.path.join(self.cache_dir, tgt0, tgt1)
		cachefile = os.path.join(cachedir, tgt2)
		if not os.path.exists(cachedir):
			try:
				os.makedirs(cachedir, 0o755)
			except OSError as ex:
				if ex.errno != errno.EEXIST:
					raise

		return cachefile

