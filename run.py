#!/usr/bin/python3
from melano import MelanoProject
from melano.c.out import COut
from optparse import OptionParser, OptionGroup
import logging
import os
import pickle
import signal
import sys


def parse_args():
	parser = OptionParser()

	build_opts = OptionGroup(parser, 'Build Options', "If these options do not give you enough freedom to correctly " + \
							"specify your python on your platform of choice, please file a bug report!")
	build_opts.add_option('-P', '--python', dest='version', default='3.1', metavar='3.X', help="Version of Python to build against")
	build_opts.add_option('-p', '--prefix', default='/usr', metavar='PREFIX', help="Where do we find python?")
	build_opts.add_option('-A', '--abi', default='', metavar='ABI', help="Python's ABI definition string (e.g. du, dmu, etc)")
	build_opts.add_option('-I', '--include', default='.*', metavar='REGEX', help="Only matching files will be considered as in the project (default: .*)")
	build_opts.add_option('-E', '--exclude', default='$^', metavar='REGEX', help="Any matching files will be considered as outside the project (default: $^)")
	parser.add_option_group(build_opts)

	gui_opts = OptionGroup(parser, 'GUI Options')
	gui_opts.add_option('-g', '--gui', action='store_true', help="Show a GUI with analysis results after building")
	parser.add_option_group(gui_opts)

	opt_opts = OptionGroup(parser, 'Optimization Options')
	opt_opts.add_option('-O', '--opt', default=None, metavar='MODE', help="Pick your poison (asp or sap)")
	opt_opts.add_option('-o', '--options', default='', metavar='OPTIONS', help="Comma separated list of build options")
	parser.add_option_group(opt_opts)

	opts, args = parser.parse_args()

	# we require the user to set the path they want to build
	if len(args) < 1:
		logging.critical("You must give run.py a file to build")
		return 1

	# we require an optimization level
	if opts.opt == 'asp':
		opts.opt = 1
	elif opts.opt == 'sap':
		opts.opt = 0
	else:
		logging.critical("You must set a valid optimization level with -O or --opt")
		#FIXME: detail optimization levels here
		return 2

	# split and cleanup the options list
	opts.options = {o.strip() for o in opts.options.split(',')}

	return opts, args


def main():
	logging.basicConfig(level=logging.INFO)
	opts, args = parse_args()

	# set version and extract paths for version
	#FIXME: this is probably highly OS specific at the moment
	if opts.version == '3.3':
		logging.info("Building against Python3.3")
		stdlib = [os.path.join(opts.prefix, 'lib', 'python3.3'), os.path.join(opts.prefix, 'lib', 'python3.3', 'lib-dynload')]
		extensions = [os.path.join(opts.prefix, 'python3.3', 'site-packages')]
	elif opts.version == '3.2':
		logging.info("Building against Python3.2")
		stdlib = [os.path.join(opts.prefix, 'lib', 'python3.2'), os.path.join(opts.prefix, 'lib', 'python3.2', 'lib-dynload')]
		extensions = [os.path.join(opts.prefix, 'python3.2', 'site-packages')]
	else:
		logging.info("Building against Python3.1")
		stdlib = [os.path.join(opts.prefix, 'lib', 'python3.1'), os.path.join(opts.prefix, 'lib', 'python3.1', 'lib-dynload')]
		extensions = [os.path.join(opts.prefix, 'python3.1', 'site-packages')]

	path = args[-1]
	base = os.path.dirname(path)
	fn = os.path.basename(path)
	project = MelanoProject('test-' + os.path.basename(path), build_dir='.')
	project.configure(programs=[fn[:-3]], roots=[base],
					stdlib=stdlib, extensions=extensions,
					prefix=opts.prefix, version=opts.version, abi=opts.abi,
					include=opts.include, exclude=opts.exclude,
					verbose=False, opt_level=opts.opt, opt_options=opts.options
				)
	project.build_one(fn[:-3], 'test.c')

	if opts.gui:
		from melano.ui.application import MelanoApplication
		app = MelanoApplication(project, sys.argv)
		signal.signal(signal.SIGINT, signal.SIG_DFL) # set default sighandler (after qapp init) so we can exit with ctrl+c
		return app.exec_()

	return 0

if __name__ == '__main__':
	sys.exit(main())

