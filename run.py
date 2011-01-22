#!/usr/bin/python3
from melano import MelanoProject
import os
import logging
import pickle

def main():
	logging.basicConfig(level=logging.INFO)

	project = MelanoProject('zeuss',
						programs=['format'],
						roots=[os.path.expanduser('~/Projects/zeuss')],
						stdlib=['/usr/lib/python3.1', '/usr/lib/python3.1/lib-dynload'],
 						extensions=['/usr/lib/python3.1/site-packages'],
 						limit=os.path.expanduser('~/Projects/zeuss') + '/format.py'
 						)
	project.locate_modules()
	project.index_names()
	project.link_references()
	project.derive_types()
	project.emit_code()


if __name__ == '__main__':
	main()

