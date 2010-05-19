#!/usr/bin/python3
'''
melinto.py
	Lint a python source file.
'''
__author__ = 'Terrence Cole <terrence@zettabytestorage.com>'


if __name__ == '__main__':
	import optparse
	import sys
	from tokenize import detect_encoding
	from melano.config.config import MelanoConfig

	# parse the command line
	parser = optparse.OptionParser('melinto')
	options, args = parser.parse_args()

	# load the configuration
	config = MelanoConfig()

	# lint each given file
	for filename in args:
		print(filename)

		# read the file contents, obeying the python encoding marker
		try:
			with open(filename, 'rb') as fp:
				encoding, _ = detect_encoding(fp.readline)
		except SyntaxError as ex:
			print(str(ex))
			sys.exit(1)
		try:
			with open(filename, 'rt', encoding=encoding) as fp:
				content = fp.read()
		except UnicodeDecodeError as ex:
			print(str(ex))
			sys.exit(1)

		tokens = config.interpreters['3.1'].parser.tokenizer.tokenize(content)
		for tok in tokens:
			print(config.interpreters['3.1'].parser.grammar.TOKEN_MAP[tok.type])
			#print(tok)

