#!/usr/bin/python3
from melano import MelanoProject
from melano.c.out import COut
import logging
import os
import pickle
import signal
import sys

def main():
	logging.basicConfig(level=logging.INFO)

	if '3.3' in sys.argv:
		logging.info("Building against Python3.3")
		stdlib = ['/usr/local/lib/python3.3', '/usr/local/lib/python3.3/lib-dynload']
		extensions = ['/usr/lib/python3.3/site-packages']
	else:
		logging.info("Building against Python3.1")
		stdlib = ['/usr/lib/python3.1', '/usr/lib/python3.1/lib-dynload']
		extensions = ['/usr/lib/python3.1/site-packages']

	# some tests
	if len(sys.argv) < 2:
		pass

	path = sys.argv[-1]
	base = os.path.dirname(path)
	fn = os.path.basename(path)
	project = MelanoProject('test-' + os.path.basename(path), build_dir='.')
	project.configure(programs=[fn[:-3]], roots=[base], verbose=False, stdlib=stdlib, extensions=extensions)
	project.build_one(fn[:-3], 'test.c')

	if 'gui' in sys.argv:
		from melano.ui.application import MelanoApplication
		app = MelanoApplication(project, sys.argv)
		signal.signal(signal.SIGINT, signal.SIG_DFL) # set default sighandler (after qapp init) so we can exit with ctrl+c
		return app.exec_()

	return 0

if __name__ == '__main__':
	sys.exit(main())

