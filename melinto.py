#!/usr/bin/python3
'''
melinto.py
	Lint a python source file.
'''
__author__ = 'Terrence Cole <terrence@zettabytestorage.com>'


if __name__ == '__main__':
	import sys
	from tokenize import detect_encoding

	filename = sys.argv[1]
	
	# read the file contents
	with open(filename, 'rb') as fp:
		encoding, _ = detect_encoding(fp.readline)
	with open(filename, 'rt', encoding=encoding) as fp:
		content = fp.read()
	print(content)

