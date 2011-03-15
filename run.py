#!/usr/bin/python3
from melano import MelanoProject
from melano.c.out import COut
import logging
import os
import pickle
import signal
import sys
#from melano.ui.application import MelanoApplication

def main():
	logging.basicConfig(level=logging.INFO)

	# some tests
	if len(sys.argv) > 1:
		files = sys.argv[1:]
		for path in files:
			base = os.path.dirname(path)
			fn = os.path.basename(path)
			project = MelanoProject('test', programs=[fn[:-3]], roots=[base])
			project.configure(limit='', verbose=False)
			project.build('test.c')
		return

	#app = MelanoApplication(project, sys.argv)
	#signal.signal(signal.SIGINT, signal.SIG_DFL) # set default sighandler (after qapp init) so we can exit with ctrl+c
	#return app.exec_()

if __name__ == '__main__':
	main()

