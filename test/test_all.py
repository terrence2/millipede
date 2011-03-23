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
	if "testfile" in metafunc.funcargnames:
		for root, _, files in os.walk('test'):
			for fn in files:
				if fn.endswith('.py') and not fn.startswith('_') and fn != 'test_all.py':
					path = os.path.join(root, fn)
					metafunc.addcall(funcargs=dict(testfile=path, root=root), id=path)


def test_all(testfile, root):
	expect = load_expectations(testfile)
	if expect['xfail']:
		pytest.xfail()

	fn = os.path.basename(testfile)
	project = MelanoProject('test', programs=[fn[:-3]], roots=[root])
	#project.configure(limit=testfile, verbose=False)
	project.configure(limit='', verbose=False)
	project.build('test.c')

	p = subprocess.Popen(['make'])
	out = p.communicate()
	assert p.returncode == 0, "Failed Make: {}".format(out)

	p = subprocess.Popen([os.path.join(TESTDIR, 'test-prog')], stderr=subprocess.PIPE, stdout=subprocess.PIPE)
	out = p.communicate()
	assert p.returncode == expect['returncode']
	if not expect['skip_io']:
		assert filter_output(out[0]) == expect['stdout']
		assert filter_output(out[1]) == expect['stderr']
	if expect['no_external']:
		with open('test.c', 'r') as fp:
			assert len([ln for ln in fp if 'PyImport_ImportModule' in ln]) <= 1

def filter_output(data:bytes) -> [str]:
	out = data.strip().decode('UTF-8').split('\n') # turn into text lines
	return [o.strip() for o in out if o and not re.match(r'\[\d+ refs\]', o)] # remove empty elements


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

