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
	from melano.code.unit import MelanoCodeUnit
	from melano.parser.pgen.parser import ParseError

	# parse the command line
	parser = optparse.OptionParser('melinto')
	options, args = parser.parse_args()

	# load the configuration
	config = MelanoConfig()

	# lint each given file
	for filename in args:
		config.log.info(filename)
		try:
			unit = MelanoCodeUnit(config, filename)
			unit.get_scopes()
		except ParseError as ex:
			try:
				print(str(ex))
			except UnicodeEncodeError:
				print("Invalid unicode in parse!")
			sys.exit(1)



