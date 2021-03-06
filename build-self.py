#!/usr/bin/python3
from melano import MpProject
import logging
import os
import pickle
import signal
import sys
#from melano.ui.application import MpApplication

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

	project = MpProject('melano')
	project.configure(programs=['run'], roots=[os.path.realpath('.')], stdlib=stdlib, extensions=extensions)
	project.build_all()

	#app = MpApplication(project, sys.argv)
	#signal.signal(signal.SIGINT, signal.SIG_DFL) # set default sighandler (after qapp init) so we can exit with ctrl+c
	#return app.exec_()

if __name__ == '__main__':
	main()


