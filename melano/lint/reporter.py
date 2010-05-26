'''
Unified lint message reporting framework.
'''
__author__ = 'Terrence Cole <terrence@zettabytestorage.com>'


def report(config, unit, msg):
	lvl = msg.level[0].capitalize()
	if msg.location:
		locflags = ' [{}, {}] {}'.format(lvl, msg.location, msg.msg_name)
	else:
		locflags = ' [{}] {}'.format(lvl, msg.msg_name)

	parts = [
		unit.raw_filename, # the file
		str(msg.context.startpos[0]), # line number
		locflags, # type and loc
	]
	print(':'.join(parts))
	
