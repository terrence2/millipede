#!/usr/bin/python3
from melano import MelanoProject
import os
import logging
import pickle

def main():
	logging.basicConfig(level=logging.INFO)

	project = MelanoProject('zeuss', ['format'],
						[os.path.expanduser('~/Projects/zeuss')],
						['/usr/lib/python3.1', '/usr/lib/python3.1/lib-dynload'],
 						['/usr/lib/python3.1/site-packages']
 						)
	project.locate_modules()
	project.index_names()
	project.link_references()


if __name__ == '__main__':
	main()

