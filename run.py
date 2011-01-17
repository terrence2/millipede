#!/usr/bin/python3
from melano import MelanoProject
import os
import logging

def main():
	logging.basicConfig(level=logging.DEBUG)

	project = MelanoProject('zeuss',
						[os.path.expanduser('~/Projects/zeuss'),
						 '/usr/lib/python3.1',
						 '/usr/lib/python3.1/lib-dynload',
						 '/usr/lib/python3.1/site-packages',
						],
						['format'])
	project.locate_modules()


if __name__ == '__main__':
	main()

