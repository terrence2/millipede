'''
Copyright (c) 2011, Terrence Cole.
All rights reserved.
'''
import os
import sys
TESTDIR = os.path.realpath('.')
sys.path = [TESTDIR] + sys.path

from contextlib import contextmanager
from melano.project.project import MelanoProject
import pytest
import re
import shutil
import subprocess



def pytest_generate_tests(metafunc):
	for interpreter in ('millipede', 'hosted', 'python'):
		for version in ('3.1', '3.2', '3.3'):
			tests = []
			if "testfile" in metafunc.funcargnames:
				for root, _, files in os.walk('test'):
					for fn in files:
						if fn.endswith('.py') and not fn.startswith('_') and fn != 'test_all.py':
							path = os.path.join(root, fn)
							tests.append((path, root))
			tests.sort()
			for path, root in tests:
				id = interpreter + ':' + version + ':' + path
				print(id)
				metafunc.addcall(funcargs=dict(testfile=path, root=root, interpreter=interpreter, version=version), id=id)


def test_all(testfile, root, interpreter, version):
	expect = load_expectations(testfile)

	if interpreter == 'millipede':
		if expect['xfail']:
			pytest.xfail()

		p = subprocess.Popen(['python' + version, 'run.py', '-P', version, '-O', 'asp', testfile], stderr=subprocess.PIPE, stdout=subprocess.PIPE)
		p.communicate()
		assert p.returncode == 0, "Failed melano-x build for {}".format(testfile)

		#fn = os.path.basename(testfile)
		#project = MelanoProject('test', programs=[fn[:-3]], roots=[root])
		#project.configure(limit='', verbose=False)
		#project.build('test.c')

		p = subprocess.Popen(['make'])
		out = p.communicate()
		assert p.returncode == 0, "Failed Make: {}".format(out)

		p = subprocess.Popen([os.path.join(TESTDIR, 'test-prog')], stderr=subprocess.PIPE, stdout=subprocess.PIPE)

	elif interpreter == 'hosted':
		if expect['xfail']:
			pytest.xfail()

		p = subprocess.Popen([os.path.join(TESTDIR, 'millipede-x-' + version), testfile], stderr=subprocess.PIPE, stdout=subprocess.PIPE)
		p.communicate()
		assert p.returncode == 0, "Failed melano-x build for {}".format(testfile)

		p = subprocess.Popen(['make'])
		out = p.communicate()
		assert p.returncode == 0, "Failed Make: {}".format(out)

		p = subprocess.Popen([os.path.join(TESTDIR, 'test-prog')], stderr=subprocess.PIPE, stdout=subprocess.PIPE)

	elif interpreter.startswith('python'):
		p = subprocess.Popen(['python' + version, testfile], stderr=subprocess.PIPE, stdout=subprocess.PIPE)

	out = p.communicate()
	assert p.returncode == expect['returncode']
	actual_stdout, mem_used = filter_output(out[0])
	actual_stderr, _ = filter_output(out[1])
	assert mem_used == 0
	if not expect['skip_io']:
		assert actual_stdout == expect['stdout']
		assert actual_stderr == expect['stderr']
	if interpreter == 'melano' and expect['no_external']:
		with open('test.c', 'r') as fp:
			assert len([ln for ln in fp if 'PyImport_ImportModule' in ln]) <= 1

def filter_output(data:bytes) -> [str]:
	raw = data.strip().decode('UTF-8').split('\n') # turn into text lines
	out = []
	mem_used = 0
	for line in raw:
		line = line.strip()
		if not line: continue
		if re.match(r'\[\d+ refs\]', line): continue
		if line.startswith('DBG_excess_mem: '):
			mem_used = int(line[len('DBG_excess_mem: '):])
			continue
		out.append(line)

	return out, mem_used



def load_expectations(testfile):
	out = {
		'stdout': [],
		'stderr': [],
		'returncode': 0,
		'xfail': False,
		'skip_io': False,
		'no_external': False,
	}
	with open(testfile, 'r') as fp:
		for ln in fp:
			if ln.startswith('#out: '):
				out['stdout'].append(ln[6:].strip())
			elif ln.startswith('#err: '):
				out['stderr'].append(ln[6:].strip())
			elif ln.startswith('#returncode: '):
				out['returncode'] = int(ln[13:].strip())
			elif ln.startswith('#fail'):
				out['xfail'] = True
			elif ln.startswith('#skip_io'):
				out['skip_io'] = True
			elif ln.startswith('#no_external'):
				out['no_external'] = True
	return out

