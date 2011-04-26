'''
Copyright (c) 2011, Terrence Cole.
All rights reserved.
'''
from melano.hl.module import MelanoModule
from melano.project.analysis.find_links import FindLinks
import logging
import melano.py.ast as py
import os
import pdb
import pickle


class NoSuchModuleError(Exception):
	'''Raised when we can't find a module.'''


class ImportLoop(Exception):
	def __init__(self, filename):
		self.filename = filename


class Importer:
	def __init__(self, project, roots:[str], stdlib:[str], extensions:[str], builtins:[str], overrides:[str]):
		super().__init__()

		self.project = project
		self.roots = roots
		self.stdlib = stdlib
		self.extensions = extensions
		self.builtins = builtins
		self.overrides = overrides

		# don't loop
		self._visited = set()
		self._renames = {}

		# outputs
		self.out = []


	def trace_import_tree(self, initial_modname):
		'''
		Generate tuples of modnames, filenames, type, and the visitor.  This list will contain the source of all files 
		that may possibly be referenced on any platform at any time by use of initial_path.  In general, this will 
		be a much larger set of files than is actually used, but is the minimum set needed for static analysis of 
		the program at initial_path.
		'''
		logging.debug("Tracing: {}".format(initial_modname))
		absolute_modfile, base_location, module_type = self.find_best_path_for_modname(initial_modname)

		# don't loop
		if absolute_modfile in self._visited:
			return absolute_modfile
		self._visited.add(absolute_modfile)

		# get the package directory for where we found the module
		package_directory = os.path.dirname(absolute_modfile)

		# check for opaque finds and skip them
		logging.debug("Found file: {}".format(absolute_modfile))
		if not absolute_modfile.endswith('.py'):
			logging.debug("Opaque: {}".format(absolute_modfile))
			self.out.append((initial_modname, absolute_modfile, module_type, {}, None))
			return absolute_modfile

		# visit and pull out refs and renames
		renames, ref_paths, ast = self.find_links(initial_modname, absolute_modfile, package_directory, base_location)

		# update our global output struct
		self._renames[initial_modname] = renames
		out = (initial_modname, absolute_modfile, module_type, ref_paths, ast)
		self.out.append(out)

		return absolute_modfile


	def find_links(self, initial_modname, absolute_modfile, package_directory, base_location):
		logging.info("Scanning: {} -> {}".format(initial_modname, absolute_modfile))
		ref_paths = {}
		ast = self.project.get_file_ast(absolute_modfile)

		data = self.project.global_cache.query_file_links(absolute_modfile)
		if data is None:
			visitor = FindLinks()
			visitor.visit(ast)
			imports, importfroms, renames = visitor.imports, visitor.importfroms, visitor.renames
			self.project.global_cache.update_file_links(absolute_modfile, pickle.dumps((imports, importfroms, renames)))
		else:
			imports, importfroms, renames = pickle.loads(data)

		for alias_name in imports:
			for modname in self.__import_name_parts(alias_name):
				last = None
				try:
					last = self.trace_import_tree(modname)
				except NoSuchModuleError as ex:
					logging.critical("Failed to find module: {}".format(str(ex)))
				assert last is not None
				ref_paths[modname] = last

		for imp_level, imp_module, imp_names in importfroms:
			# find absolute module name
			rel_pkg_or_mod_name = '.' * imp_level + str(imp_module)
			abs_pkg_or_mod_name = self.find_absolute_modname(rel_pkg_or_mod_name, package_directory, base_location)

			# fetch info on module and all children
			last = None
			try:
				last = self.trace_import_tree(abs_pkg_or_mod_name)
			except NoSuchModuleError as ex:
				logging.critical("Failed to find module: {}".format(str(ex)))
			assert last is not None
			ref_paths[rel_pkg_or_mod_name] = last

			# Note: the names in the from . import <names> may be either names in the module we just added, 
			#		or they may also be modules under the package, if it is a package we just imported
			if last.endswith('__init__.py'):
				for alias_name in imp_names:
					try:
						self.trace_import_tree(abs_pkg_or_mod_name + '.' + str(alias_name))
					except NoSuchModuleError:
						logging.warning("Skipping module named: {} as possibly masked".format(abs_pkg_or_mod_name + '.' + str(alias_name)))

		return renames, ref_paths, ast


	def find_absolute_modname(self, maybe_rel_modname, package_directory, base_dir):
		'''
		Given a module name and the package directory it was found in _and_ the base directory
		where we located the package in, e.g. from some other import: convert the relative module 
		name into an absolute module name.
		'''
		if not maybe_rel_modname.startswith('.'):
			return maybe_rel_modname

		starting_rel_modname = maybe_rel_modname
		starting_package_dir = package_directory

		# strip the base_dir from the left of the package directory
		assert package_directory.startswith(base_dir)
		package_directory = package_directory[len(base_dir):]
		if package_directory.startswith('/'):
			package_directory = package_directory[1:]

		# split the package into parts by component
		package_parts = [p for p in package_directory.split('/') if p]

		# the first dot refers to items in the current package
		maybe_rel_modname = maybe_rel_modname[1:]

		# walk up in the package path until we are out of dot's
		while maybe_rel_modname.startswith('.'):
			if not package_parts:
				raise ImportError("Relative import outside of the package")
			package_parts = package_parts[:-1]
			maybe_rel_modname = maybe_rel_modname[1:]

		# the real module name is the remainder of the package and the remainder of the modname
		from_base_parts = [] if not maybe_rel_modname else maybe_rel_modname.split('.')
		absolute_modname = '.'.join(package_parts + from_base_parts)
		logging.debug("Found rel modname: {} from {} in {}".format(absolute_modname, starting_rel_modname, starting_package_dir))
		return absolute_modname


	def __import_name_parts(self, alias_name):
		'''
		When we want to import, for example, os.path, we need to run the os.path code, but we also
		need to get the module 'os' so that we can attach that module into the namespace.  This function
		breaks appart attribute module names and yields each module we need to load.
		'''
		if '.' in alias_name:
			parts = []
			for name in alias_name.split('.'):
				parts.append(name)
				yield '.'.join(parts)
		else:
			yield alias_name


	def __get_renamed_modname(self, parent_modname, target_modname):
		# check the cache
		if parent_modname in self._renames:
			renames = self._renames[parent_modname].get(target_modname)
		# otherwise, lookup and send visitor against the module
		else:
			absolute_modfile, base_location, module_type = self.find_best_path_for_modname(parent_modname)
			assert absolute_modfile.endswith('.py'), 'Renamed modname encounted non-py file'
			ast = self.project.get_file_ast(absolute_modfile)
			visitor = FindLinks()
			visitor.visit(ast)
			renames = visitor.renames.get(target_modname)
		if not renames:
			raise NoSuchModuleError("looking for {} in {}".format(target_modname, parent_modname))

		if len(renames) == 1:
			renamed = renames[0]
		else:
			# TODO: can we pick the right one here in common cases?
			# for now just take one... doesn't matter too much which if they expose the same interface
			renamed = renames[0]

		return renamed


	def find_best_path_for_modname(self, initial_modname):
		try:
			absolute_modfile, base_location, module_type = self.project.cache.get_module_path(initial_modname)
			return absolute_modfile, base_location, module_type
		except KeyError:
			try:
				# find the modname on the filesystem
				absolute_modfile, base_location, module_type = self.find_best_path_for_absolute_modname(initial_modname)
			except NoSuchModuleError:
				# if not in the filesystem, look for a module renamed into the parent's dict
				absolute_modfile, base_location, module_type = self.find_best_path_for_relocated_modname(initial_modname)
			self.project.cache.add_module_location(initial_modname, absolute_modfile, base_location, module_type)
			return absolute_modfile, base_location, module_type


	def find_best_path_for_absolute_modname(self, modname):
		'''
		Return a tuple of absolute_filename and type.
		'''
		search = [
			(MelanoModule.PROJECT, self.roots),
			(MelanoModule.BUILTIN, self.builtins),
			(MelanoModule.STDLIB, self.stdlib),
			(MelanoModule.EXTENSION, self.extensions)
		]
		rel_noext_modpath = modname.replace('.', '/')
		for ty, base_paths in search:
			for base_path in base_paths:
				base_path = os.path.realpath(base_path)
				trial_abs_noext_modpath = os.path.join(base_path, rel_noext_modpath)
				# 1) assume modpath refers directly to a file 
				for ext in ['.py']:
					trial_abs_modpath = trial_abs_noext_modpath + ext
					logging.debug("looking for {}".format(trial_abs_modpath))
					if os.path.exists(trial_abs_modpath):
						return trial_abs_modpath, base_path, ty
				# 2) modpath might refer to a directory / package, so try with __init__
				trial_abs_modpath = os.path.join(trial_abs_noext_modpath, '__init__.py')
				logging.debug("looking for {}".format(trial_abs_modpath))
				if os.path.exists(trial_abs_modpath):
					return trial_abs_modpath, base_path, ty

		raise NoSuchModuleError(modname)


	def find_best_path_for_relocated_modname(self, modname):
		# if we have no parent, then there is nothing to look for
		if '.' not in modname:
			raise NoSuchModuleError(modname)

		# split out the parent modname and the target within it
		parent_modname, _, target_modname = modname.rpartition('.')
		renamed = self.__get_renamed_modname(parent_modname, target_modname)

		# need to look adjacent to the parent
		if '.' in parent_modname:
			gparent_modname, _, _ = parent_modname.rpartition('.')
			real_modname = gparent_modname + '.' + renamed
		else:
			real_modname = renamed

		# restart the search for the original name, but in the new location
		return self.find_best_path_for_absolute_modname(real_modname)
