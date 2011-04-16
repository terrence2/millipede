#!/usr/bin/python3
'''
Copyright (c) 2011, Terrence Cole.
All rights reserved.
'''
from melano import MelanoProject
import logging
import optparse
import os
import pickle
import signal
import sys
#from melano.ui.application import MelanoApplication

def main():
	logging.basicConfig(level=logging.INFO)

	base_stdlib = [os.path.realpath('../py3benchmarks/lib')]

	parser = optparse.OptionParser()
	parser.add_option('-b', '--benchmarks')
	options, args = parser.parse_args()

	if '3.3' in args:
		logging.info("Building against Python3.3")
		stdlib = base_stdlib + ['/usr/local/lib/python3.3', '/usr/local/lib/python3.3/lib-dynload']
		extensions = ['/usr/lib/python3.3/site-packages']
	else:
		logging.info("Building against Python3.1")
		stdlib = base_stdlib + ['/usr/lib/python3.1', '/usr/lib/python3.1/lib-dynload']
		extensions = ['/usr/lib/python3.1/site-packages']

	programs = ['bm_float', 'bm_pidigits']
	if options.benchmarks:
		programs = [p.strip() for p in options.benchmarks.split(',')]

	project = MelanoProject('benchmarks', programs=programs, roots=[os.path.realpath('../py3benchmarks/performance')])
	project.configure(stdlib=stdlib, extensions=extensions)
	project.build_all()

	#app = MelanoApplication(project, sys.argv)
	#signal.signal(signal.SIGINT, signal.SIG_DFL) # set default sighandler (after qapp init) so we can exit with ctrl+c
	#return app.exec_()

if __name__ == '__main__':
	main()


