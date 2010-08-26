#!/usr/bin/python3.1
import sys
import signal
from melano.ui.application import MelanoApplication
from melano.ui.main import MelanoMainWindow


def main():
	app = MelanoApplication(sys.argv)
	
	# set default sighandler (after qapp init) so we can exit with ctrl+c
	signal.signal(signal.SIGINT, signal.SIG_DFL)

	return app.exec_()


if __name__ == '__main__':
	sys.exit(main())
