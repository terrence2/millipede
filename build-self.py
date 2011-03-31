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

	project = MelanoProject('melano', programs=['run'], roots=[os.path.expanduser('~/Projects/melano')])
	project.configure()
	project.build('build/melano.c')

	#app = MelanoApplication(project, sys.argv)
	#signal.signal(signal.SIGINT, signal.SIG_DFL) # set default sighandler (after qapp init) so we can exit with ctrl+c
	#return app.exec_()

if __name__ == '__main__':
	main()


