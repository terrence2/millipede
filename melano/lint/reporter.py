'''
Unified lint message reporting framework.
'''
__author__ = 'Terrence Cole <terrence@zettabytestorage.com>'


def report(config, unit, msg):
	if config.project.lint_message_is_masked(msg.__class__.__name__):
		return

	lvl = msg.__class__.__name__[0].capitalize()
	doc = msg.__doc__.format(*msg.extra)
	if msg.location:
		locflags = ' [{}, {}] {}'.format(lvl, msg.location, doc)
	else:
		locflags = ' [{}] {}'.format(lvl, doc)

	parts = [
		unit.filename[len(config.project.base_dir) + 1:], # the file
		str(msg.context.startpos[0]), # line number
		locflags, # type and loc
	]
	print(':'.join(parts))
	
