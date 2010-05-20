#!/usr/bin/python3
'''
melinto.py
	Lint a python source file.
'''
__author__ = 'Terrence Cole <terrence@zettabytestorage.com>'


if __name__ == '__main__':
	import optparse
	import sys
	from melano.config.config import MelanoConfig
	from melano.parser.pgen.parser import ParseError

	# parse the command line
	parser = optparse.OptionParser('melinto')
	options, args = parser.parse_args()

	# load the configuration
	config = MelanoConfig()

	# lint each given file
	for filename in args:
		print(filename)
		try:
			ast = config.interpreters['3.1'].parser.parse_file(filename)
		except ParseError as ex:
			try:
				print(str(ex))
			except UnicodeEncodeError:
				print("Invalid unicode in parse!")
			sys.exit(1)

