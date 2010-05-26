#!/usr/bin/python3
from distutils.core import setup

VERSION = '0.0.0'
setup(
	name='melano',
	version=VERSION,
	description='a python programmaing toolkit',
	author='Terrence Cole',
	author_email='terrence@zettabytestorage.com',
	packages=[
		'melano',
		'melano/code',
		'melano/code/utils',
		'melano/config',
		'melano/lint',
		'melano/lint/fluff',
		'melano/parser',
		'melano/parser/common',
		'melano/parser/pgen',
		'melano/parser/py3',
		'melano/util',
	],
	scripts=[
		'melinto',
	],
	data_files=[
		('/usr/share/melano-' + VERSION + '/grammar', 
			['data/grammar/python-3.1']
		),
	],
	ext_package="",
	ext_modules=[]
)
