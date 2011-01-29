'''
Copyright (c) 2011, Terrence Cole.
All rights reserved.
'''
from melano.project.lowlevel.target import Target, EntryPoint
import os.path


class Makefile:
	def __init__(self, builddir:str, roots:[str]):
		self.builddir = builddir
		self.roots = roots
		self.filename = os.path.join(builddir, 'Makefile')
		self.programs = []
		self.targets = []

		if not os.path.isdir(self.builddir):
			os.makedirs(self.builddir, 0o755)


	def __find_root(self, filename):
		for root in self.roots:
			if filename.startswith(root):
				return root
		raise ValueError("File {} is not in roots: {}".format(filename, self.roots))


	def __canonical_names(self, root, filename):
		if not filename.endswith('.py'):
			raise ValueError("Trying to emit next to non-py module")
		base = filename[len(root) + 1:-3]
		base.replace('/', '_')
		fn = os.path.join(self.builddir, base)
		return base, fn + '.c', fn + '.h'


	def add_program(self, program, filename):
		root = self.__find_root(filename)
		base, body, hdr = self.__canonical_names(root, filename)
		tgt = EntryPoint(program, base, body, hdr)
		self.targets.append(tgt)
		self.programs.append(program)
		return tgt


	def add_source(self, filename):
		'''
		Given the filename of a python module, adds code to the makefile to build and cleanup the
			generated sources.  Returns a target instance to use when emitting code..
		'''
		root = self.__find_root(filename)
		base, body, hdr = self.__canonical_names(root, filename)
		tgt = Target(base, body, hdr)
		self.targets.append(tgt)
		return tgt


	def c_sources(self):
		return [t.bodyname[len(self.builddir) + 1:] for t in self.targets]


	def c_headers(self):
		return [t.headername[len(self.builddir) + 1:] for t in self.targets]


	def write(self):
		args = {
			'programs': ' '.join(self.programs),
			'c_sources': ' '.join(self.c_sources()),
			'all_sources': ' '.join(self.c_headers() + self.c_sources())
		}
		with open(self.filename, 'w') as fp:
			fp.write("""#Generated by Melano
all: {programs}
	 
clean:
	rm -f {programs}

mrproper: clean
	rm -f {all_sources}
	rm -f Makefile
""".format(**args))

			for prog in self.programs:
				fp.write("""
{prog}: 
	gcc `python-config-3.1 --cflags` `python-config-3.1 --libs` -o {prog} {c_sources}
""".format(prog=prog, **args))
