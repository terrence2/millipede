#!/usr/bin/python3
from melano import MelanoProject
import logging
import os
import pickle
import signal
import sys
#from melano.ui.application import MelanoApplication

def main():
	logging.basicConfig(level=logging.INFO)

	if 'py33' in sys.argv:
		logging.info("Building against Python3.3")
		stdlib = ['/usr/local/lib/python3.3', '/usr/local/lib/python3.3/lib-dynload']
		extensions = ['/usr/lib/python3.3/site-packages']
	else:
		logging.info("Building against Python3.1")
		stdlib = ['/usr/lib/python3.1', '/usr/lib/python3.1/lib-dynload']
		extensions = ['/usr/lib/python3.1/site-packages']

	project = MelanoProject('melano', programs=['run'], roots=[os.path.expanduser('~/Projects/melano')])
	project.configure(stdlib=stdlib, extensions=extensions)
	project.build('melano.c')

	#app = MelanoApplication(project, sys.argv)
	#signal.signal(signal.SIGINT, signal.SIG_DFL) # set default sighandler (after qapp init) so we can exit with ctrl+c
	#return app.exec_()

if __name__ == '__main__':
	main()


