'''
Copyright (c) 2011, Terrence Cole.
All rights reserved.
'''
from collections import namedtuple
import textwrap

class Makefile:

	_Target = namedtuple('_Target', 'name source')


	def __init__(self, filename:str, data_dir:str, *, prefix, version, abi):
		self.filename = filename
		self.data_dir = data_dir
		self.targets = []

		self.prefix = prefix
		self.version = version
		self.abi = abi


	def add_target(self, name, source):
		self.targets.append(self._Target(name, source))


	def write(self):
		with open(self.filename, 'w') as fp:
			fp.write('# Makefile, autogenerated by Millipede\n')

			fp.write(textwrap.dedent('''
				GCC=gcc
				CFLAGS=-DCORO_UCONTEXT
				CFLAGS_WARN=-Wall -Wno-unused-label -Wtrigraphs
				CFLAGS_OPT=-O0 -g
				CFLAGS_PROF=-fprofile-arcs -ftest-coverage -pg
				CFLAGS_INCLUDE=-I{prefix}/include -I{data_dir}/c -I{data_dir}/c/libcoro
				ABI={abi}
				
				EXTRA_SOURCES={data_dir}/c/env.c {data_dir}/c/closure.c {data_dir}/c/funcobject.c {data_dir}/c/genobject.c {data_dir}/c/libcoro/coro.c
				LIBS=-pthread -lm -ldl -lutil
				
			'''.format(data_dir=self.data_dir, prefix=self.prefix, abi=self.abi)))

			fp.write("all: {}\n".format(' '.join([target.name for target in self.targets])))
			fp.write('\t\n\n')

			fp.write("prof: {}\n".format(' '.join([target.name + '-prof' for target in self.targets])))
			fp.write('\t\n\n')

			fp.write("clean: {}\n".format(' '.join(['clean_' + target.name for target in self.targets])))
			fp.write('\t\n\n')

			for target in self.targets:
				self._write_target(target, fp)


	def _write_target(self, target, fp):
		config = {
			'prefix': self.prefix,
			'version': self.version,
			'abi': self.abi
		}
		args = {
			'includes': '-I{prefix}/include/python{version}{abi}'.format(**config),
			'libs': '-lpython{version}{abi}'.format(**config),
			'output': target.name,
			'source': target.source,
		}
		fp.write('{}: Makefile {}.c\n'.format(target.name, target.name))
		fp.write(('\t${{GCC}} ${{CFLAGS}} ${{CFLAGS_WARN}} ${{CFLAGS_OPT}} ${{CFLAGS_INCLUDE}}' +
				' {includes} -o {output} {source} ${{EXTRA_SOURCES}} {libs} ${{LIBS}}\n\n').format(**args))

		fp.write('{}: Makefile {}.c\n'.format(target.name + '-prof', target.name))
		fp.write(('\t${{GCC}} ${{CFLAGS}} ${{CFLAGS_WARN}} ${{CFLAGS_OPT}} ${{CFLAGS_PROF}} ${{CFLAGS_INCLUDE}}' +
				' {includes} -o {output} {source} ${{EXTRA_SOURCES}} {libs} ${{LIBS}}\n\n').format(**args))

		fp.write('clean_{}:\n'.format(target.name))
		fp.write('\t-rm {}\n'.format(target.name))
		fp.write('\n')