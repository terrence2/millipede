#!/usr/bin/python3
'''
melinto.py
	Run melano's linting backend detached from the GUI.
'''
__author__ = 'Terrence Cole <terrence@zettabytestorage.com>'


if __name__ == '__main__':
	import os
	import sys
	from melano.config.config import MelanoConfig
	from melano.py.pgen.parser import ParseError
	from melano.lint import lint, report

	# load the configuration
	config = MelanoConfig()

	def lint_one_unit(unit):
		config.log.info(unit.filename)

		try:
			msgs = lint(unit)
		except ParseError as ex:
			try:
				print(str(ex))
			except UnicodeEncodeError:
				print("Invalid unicode in parse!")
			sys.exit(1)
		
		# do the main linting business
		for msg in msgs:
			report(config, unit, msg)

		# preserve the unit, since we went to all the trouble of parsing it
		unit.freeze()
		
		# return the number of messages generated
		return len(msgs)

	# lint each file from the command line
	count = 0
	for modname, unit in config.project.units.items():
		count += lint_one_unit(unit)
	

	print()
	print("Report")
	print("======")
	print("Found", count, "problems")

