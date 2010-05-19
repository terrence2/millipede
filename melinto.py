#!/usr/bin/python3
'''
melinto.py
	Lint a python source file.
'''
__author__ = 'Terrence Cole <terrence@zettabytestorage.com>'


if __name__ == '__main__':
	import optparse
	import sys
	from tokenize import detect_encoding
	from melano.config.config import MelanoConfig

	# parse the command line
	parser = optparse.OptionParser('melinto')
	options, args = parser.parse_args()

	# load the configuration
	config = MelanoConfig()

	# lint each given file
	for filename in args:
		# read the file contents
		with open(filename, 'rb') as fp:
			encoding, _ = detect_encoding(fp.readline)
		with open(filename, 'rt', encoding=encoding) as fp:
			content = fp.read()
		print(content)

