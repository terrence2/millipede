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

	project = MelanoProject('zeuss', programs=['format'], roots=[os.path.expanduser('~/Projects/zeuss')])
	project.configure(limit=os.path.expanduser('~/Projects/zeuss') + '/format.py')
	project.locate_modules()
	project.index_names()
	#project.link_references()
	#project.derive_types()
	#project.emit_code()
	c = project.transform_lowlevel_0()

	with COut('test.c') as v:
		v.visit(c)


	#app = MelanoApplication(project, sys.argv)
	#signal.signal(signal.SIGINT, signal.SIG_DFL) # set default sighandler (after qapp init) so we can exit with ctrl+c
	#return app.exec_()

if __name__ == '__main__':
	main()

