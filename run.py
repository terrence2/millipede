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
	files = ['test/functions/nested_func.py']
	for path in files:
		base = os.path.dirname(path)
		fn = os.path.basename(path)
		project = MelanoProject('test', programs=[fn[:-3]], roots=[base])
		project.configure(limit=path, verbose=False)
		project.locate_modules()
		project.index_names()
		project.show()
		c = project.transform_lowlevel_0()
		with COut('test.c') as v:
			v.visit(c)
	return
	'''
	'''

	# all tests
	for root, dirs, files in os.walk('test'):
		for fn in files:
			if fn.endswith('.py'):
				path = os.path.join(root, fn)
				project = MelanoProject('test', programs=[fn[:-3]], roots=[root])
				project.configure(limit=path, verbose=False)
				project.locate_modules()
				project.index_names()
				project.show()

	return

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

