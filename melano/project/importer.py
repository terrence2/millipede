'''
Copyright (c) 2011, Terrence Cole.
All rights reserved.
'''
from melano.hl.nodes.module import MpModule
from melano.project.analysis.find_links import FindLinks
from textwrap import dedent
import logging
import melano.py.ast as py
import os
import pdb
import pickle
import subprocess
import tempfile


class ModuleDesc:
	'''Base for all module descriptors.  Modules can be found in several ways: files on disk, 
		probed in an interpretter, or simply missing.'''
	TYPE_FILE = 0
	TYPE_PROBE = 1
	TYPE_MISSING = 2

	def __init__(self, ty, modtype, modname):
		super().__init__()
		self.type = ty
		self.modtype = modtype
		self.modname = modname

	@classmethod
	def unpack(cls, ty, modtype, modname, data):
		if ty == cls.TYPE_FILE:
			path, _, directory = data.rpartition('\n')
			return ModuleFileDesc(modtype, modname, path, directory)
		elif ty == cls.TYPE_PROBE:
			names = data.split()
			return ModuleProbedDesc(modtype, modname, names)
		elif ty == cls.TYPE_MISSING:
			return ModuleMissingDesc(modtype, modname)

	def __repr__(self):
		return '<{}({})>'.format(type(self).__name__, self.modname)


class ModuleFileDesc(ModuleDesc):
	'''Describes a module that was found in a file.'''
	def __init__(self, modtype, modname, path, directory):
		super().__init__(ModuleDesc.TYPE_FILE, modtype, modname)
		self.path = path
		self.directory = directory

	def pack(self):
		return self.path + '\n' + self.directory



class ModuleProbedDesc(ModuleDesc):
	'''Describes a module that we cataloged by probing it in an interpretter.'''
	def __init__(self, modtype, modname, defined_names):
		super().__init__(ModuleDesc.TYPE_PROBE, modtype, modname)
		self.names = defined_names

	def pack(self):
		return '\n'.join(self.names)


class ModuleMissingDesc(ModuleDesc):
	'''Describes a module that we cannot find anywhere.  If the program attempts to read names from
		such a module, e.g. with an import-from, then this will fail.'''
	def __init__(self, modtype, modname):
		super().__init__(ModuleDesc.TYPE_MISSING, modtype, modname)

	def pack(self):
		return ''


class NoSuchModuleError(Exception):
	'''Raised when we can't find a module.'''

class ImportLoop(Exception):
	def __init__(self, filename):
		self.filename = filename



class Importer:
	'''Encapsulates a search through a python source tree(s) filled with packages and modules to pick out all
		modules which may be reachable.  Where modules are found that do not have a python file present where
		presented with, we attempt to probe.  Where we cannot find sources or probe, we insert a reference to
		missing symbols.
	'''

	# A perfect importer would need to run a PythonVM over the source to find out the full set of names that
	#		are available from a module.  In practice, this is only really needed in very few cases -- usually we can
	#		get away with just looking for name assignments at the global level.  In cases where there is enough
	#		dynamism to make this hard, break out the virtual machine to manually probe for exposed names. 
	QUIRK_PROBE_ONLY = {'hashlib'}

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

		# track 'as' renames in import statements so that we can find renamed modules quickly
		self._renames = {}

		# if we find a module is missing, it doesn't get "visited" so add it here at a low-level to avoid
		#		having to spawn dozens of un-needed probe processes
		self._missing = set()

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
		desc = self.find_best_path_for_modname(initial_modname)

		# don't loop
		if desc.modname in self._visited:
			return desc
		self._visited.add(desc.modname)

		# if we have no file resource, we can't easily go further
		if not isinstance(desc, ModuleFileDesc):
			self.out.append((desc, None, None))
			return desc

		# get the package directory for where we found the module
		package_directory = os.path.dirname(desc.path)

		# check for opaque finds and skip them
		logging.debug("Found file: {}".format(desc.path))
		if not desc.path.endswith('.py'):
			logging.info("Probing non-py: {}".format(desc.path))
			real_desc = self.probe_for_module_info(initial_modname)
			real_desc.modtype = desc.modtype
			self.out.append((real_desc, None, None))
			return real_desc

		# visit and pull out refs and renames
		renames, ref_paths, ast = self.find_links(initial_modname, desc.path, package_directory, desc.directory)

		# update our global output struct
		self._renames[initial_modname] = renames
		self.out.append((desc, ast, ref_paths))

		return desc


	def find_links(self, initial_modname, absolute_modfile, package_directory, base_location):
		if self.project.verbose:
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
			desc = self.trace_import_tree(abs_pkg_or_mod_name)
			ref_paths[rel_pkg_or_mod_name] = desc

			# Note: the names in the 'from . import <names>' may be either names in the module we just added, 
			#		or they may also be modules under the package, if it is a package we just imported.  If they are
			#		modules, we want to trace them too, as they are part of the import chain.
			if (isinstance(desc, ModuleFileDesc) and desc.path.endswith('__init__.py')):
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
			desc = self.find_best_path_for_modname(parent_modname)
			if not isinstance(desc, ModuleFileDesc):
				raise NoSuchModuleError("opaque module at bottom of renamed lookup")
			ast = self.project.get_file_ast(desc.path)
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
			ty, modtype, modname, data = self.project.cache.get_module_path(initial_modname)
			return ModuleDesc.unpack(ty, modtype, modname, data)
		except KeyError:
			# if the module should not be searched, but just probed directly
			if initial_modname in self.QUIRK_PROBE_ONLY:
				desc = self.probe_for_module_info(initial_modname)
			else:
				try:
					# find the modname on the filesystem
					desc = self.find_best_path_for_absolute_modname(initial_modname)
				except NoSuchModuleError:
					try:
						# if not in the filesystem, look for a module renamed into the parent's dict
						desc = self.find_best_path_for_relocated_modname(initial_modname)
					except NoSuchModuleError:
						try:
							# if we are not relocated from another module, try probing
							desc = self.probe_for_module_info(initial_modname)
						except NoSuchModuleError:
							# if nothing else works, return a fully opaque module
							logging.warning("Missing module: " + initial_modname)
							return ModuleMissingDesc(MpModule.BUILTIN, initial_modname)

			#self.project.cache.add_module_location(initial_modname, absolute_modfile, base_location, module_type)
			self.project.cache.add_module_location(desc.type, desc.modtype, desc.modname, desc.pack())
			return desc


	def find_best_path_for_absolute_modname(self, modname):
		'''
		Return a tuple of absolute_filename and type.
		'''
		search = [
			(MpModule.PROJECT, self.roots),
			#(MpModule.BUILTIN, self.builtins),
			(MpModule.STDLIB, self.stdlib),
			(MpModule.EXTENSION, self.extensions)
		]
		rel_noext_modpath = modname.replace('.', '/')
		for ty, base_paths in search:
			for base_path in base_paths:
				base_path = os.path.realpath(base_path)
				trial_abs_noext_modpath = os.path.join(base_path, rel_noext_modpath)
				# 1) assume modpath refers directly to a file 
				for ext in ['.py', '.so']:
					trial_abs_modpath = trial_abs_noext_modpath + ext
					logging.debug("looking for {}".format(trial_abs_modpath))
					if os.path.exists(trial_abs_modpath):
						return ModuleFileDesc(ty, modname, trial_abs_modpath, base_path)
				# 2) modpath might refer to a directory / package, so try with __init__
				trial_abs_modpath = os.path.join(trial_abs_noext_modpath, '__init__.py')
				logging.debug("looking for {}".format(trial_abs_modpath))
				if os.path.exists(trial_abs_modpath):
					return ModuleFileDesc(ty, modname, trial_abs_modpath, base_path)

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


	def probe_for_module_info(self, modname):
		if modname in self._missing:
			raise NoSuchModuleError("Could not find module {} with direct probe".format(modname))

		with tempfile.NamedTemporaryFile() as tmp:
			probe = dedent("""
				import sys
				print(str(sys.version_info.major) + '.' + str(sys.version_info.minor))
				import {0}
				for n in sorted(dir({0})):
					print(n)
			""".format(modname))
			probe = self._probe_quirks(modname, probe)
			tmp.write(probe.encode('UTF-8'))
			tmp.flush()
			exe0 = os.path.join(self.project.c_prefix, 'bin', 'python' + self.project.c_version)
			exe1 = os.path.join(self.project.c_prefix, 'bin', 'python')
			for exe in (exe0, exe1):
				p = subprocess.Popen([exe, tmp.name], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
				rv = p.communicate()
				if p.returncode != 0:
					continue
				lines = rv[0].decode('UTF-8').split()
				if lines[0] != self.project.c_version:
					continue
				return ModuleProbedDesc(MpModule.BUILTIN, modname, lines[1:])

		self._missing.add(modname)
		raise NoSuchModuleError("Could not find module {} with direct probe".format(modname))


	def _probe_quirks(self, modname, probe):
		'''Specially handle cases where python is simply insane.'''
		if modname == '_dummy_threading':
			# dummy_threading imports threading and sets it as _dummy_threading in the modules list, so we need to
			#	import dummy_threading to actually import _dummy_threading, or we just fail.
			probe = 'import dummy_threading\n' + probe
		return probe
