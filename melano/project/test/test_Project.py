'''
Copyright (c) 2011, Terrence Cole.
All rights reserved.
'''
from melano.project.project import MelanoProject
import os
import unittest


class TestProject(unittest.TestCase):
	def test_locate_modules(self):
		for fn in os.listdir('melano/test/samples/import'):
			project = MelanoProject(fn, [os.path.realpath('melano/test/samples/import'),
							 '/usr/lib/python3.1',
							 '/usr/lib/python3.1/lib-dynload',
							 '/usr/lib/python3.1/site-packages'],
							 [fn[:-3]])
			project.locate_modules()
