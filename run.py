#!/usr/bin/python3

if __name__ == '__main__':
	# load the configuration
	from melano.config.config import MelanoConfig
	config = MelanoConfig()

	# create a new symbol store
	from melano.code.symbols.program import Program
	db = Program(config.project.name)

	# add all units to the symbol store
	for modname, unit in config.project.units.items():
		db.add_module(modname, unit)

	print(db.as_string())

