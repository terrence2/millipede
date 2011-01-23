#!/usr/bin/python3
from melano import MelanoProject
from melano.ui.application import MelanoApplication
import logging
import os
import pickle
import signal
import sys

def main():
	logging.basicConfig(level=logging.INFO)

	project = MelanoProject('zeuss',
						programs=['format'],
						roots=[os.path.expanduser('~/Projects/zeuss')],
						stdlib=['/usr/lib/python3.1', '/usr/lib/python3.1/lib-dynload'],
 						extensions=['/usr/lib/python3.1/site-packages'],
 						limit=os.path.expanduser('~/Projects/zeuss') + '/format.py'
 						)
	project.locate_modules()
	project.index_names()
	project.link_references()
	project.derive_types()
	project.emit_code()


	app = MelanoApplication(project, sys.argv)
	signal.signal(signal.SIGINT, signal.SIG_DFL) # set default sighandler (after qapp init) so we can exit with ctrl+c
	return app.exec_()

if __name__ == '__main__':
	main()

