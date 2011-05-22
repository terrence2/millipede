'''
Copyright (c) 2011, Terrence Cole.
All rights reserved.
'''
from sqlalchemy.engine import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm.session import sessionmaker
from sqlalchemy.schema import Column, UniqueConstraint
from sqlalchemy.types import Integer, Unicode
import logging
import os.path

SQLBase = declarative_base()

class Configuration(SQLBase):
	__tablename__ = 'config'
	id = Column(Integer, primary_key=True)
	order = Column(Integer)
	key = Column(Unicode)
	value = Column(Unicode)

	def __init__(self, key, value, order=0):
		super().__init__()
		self.order = order
		self.key = key
		self.value = value

	def __lt__(self, other):
		if self.key == other.key:
			return self.order < other.order
		return self.key < other.key or self.value < other.value

	def __eq__(self, other):
		return self.value == other.value and self.key == other.key


class ModuleLocation(SQLBase):
	__tablename__ = 'module_locations'
	id = Column(Integer, primary_key=True)

	type = Column(Integer)
	modtype = Column(Integer)
	modname = Column(Unicode)
	data = Column(Unicode)

	unique_rows = UniqueConstraint('name', 'data')

	def __init__(self, type, modtype, modname, data):
		super().__init__()
		self.type = type
		self.modtype = modtype
		self.modname = modname
		self.data = data


class ProjectCache:
	def __init__(self, name, build_dir, cache_dir):
		self.name = name
		self.build_dir = build_dir
		self.cache_dir = cache_dir

		self._programs = None
		self._roots = None
		self._stdlib = None
		self._extensions = None
		self._builtins = None
		self._overrides = None

		# select the cache file
		self.cachefile = os.path.join(os.path.realpath(cache_dir), self.name) + '.db'
		logging.info("Cachefile: {}".format(self.cachefile))

		# create the sqlalchemy instances
		self.engine = create_engine('sqlite:///' + self.cachefile)
		SQLBase.metadata.create_all(self.engine)
		self.session = sessionmaker(bind=self.engine)()


	def has_same_elements(self, a, b):
		if len(a) != len(b):
			return False
		for x in a:
			if x not in b:
				return False
		return True


	def check_and_update_config_paths(self):
		'''Return true if any of the configured programs or paths changed and update the config with
			the new correct paths.'''
		programs = list(sorted(self.session.query(Configuration).filter_by(key='program_module')))
		roots = list(sorted(self.session.query(Configuration).filter_by(key='root_directory')))
		stdlib = list(sorted(self.session.query(Configuration).filter_by(key='stdlib_directory')))
		extensions = list(sorted(self.session.query(Configuration).filter_by(key='extension_directory')))
		builtins = list(sorted(self.session.query(Configuration).filter_by(key='builtin_directory')))
		overrides = list(sorted(self.session.query(Configuration).filter_by(key='override_directory')))

		# if all matching, no config change
		if [p.value for p in programs] == self._programs and \
			[d.value for d in roots] == self._roots and \
			[d.value for d in stdlib] == self._stdlib and \
			[d.value for d in extensions] == self._extensions and \
			[d.value for d in builtins] == self._builtins and \
			[d.value for d in overrides] == self._overrides:
			return False

		# delete the configuration and re-add all values
		self.session.query(Configuration).delete()
		for i, program in enumerate(self._programs):
			self.session.add(Configuration('program_module', program, i))
		for i, d in enumerate(self._roots):
			self.session.add(Configuration('root_directory', d, i))
		for i, d in enumerate(self._stdlib):
			self.session.add(Configuration('stdlib_directory', d, i))
		for i, d in enumerate(self._extensions):
			self.session.add(Configuration('extension_directory', d, i))
		for i, d in enumerate(self._builtins):
			self.session.add(Configuration('builtin_directory', d, i))
		for i, d in enumerate(self._overrides):
			self.session.add(Configuration('override_directory', d, i))
		self.session.commit()
		return True


	def prepare(self, programs, roots, stdlib, extensions, builtins, override):
		self._programs = programs
		self._roots = roots
		self._stdlib = stdlib
		self._extensions = extensions
		self._builtins = builtins
		self._overrides = override

		# if any of our configured paths have changed, we need to drop the path mapping cache
		if self.check_and_update_config_paths():
			logging.info("Cache: config invalid -- clearing")
			self.session.query(ModuleLocation).delete()
			#FIXME: other tables here, probably


	def get_module_path(self, dottedname):
		rows = self.session.query(ModuleLocation).filter_by(modname=dottedname).all()

		# NOTE: if we have more than one reference to this raw name (e.g. if it is a relative name .foo
		#	from more than one project directory), then there is not much we can do here and we need
		#	to go ahead and resolve the full name the hard way.
		if len(rows) != 1:
			raise KeyError

		row = rows[0]
		return row.type, row.modtype, row.modname, row.data


	def add_module_location(self, type, modtype, modname, data):
		row = ModuleLocation(type, modtype, modname, data)
		self.session.add(row)
		self.session.commit()
