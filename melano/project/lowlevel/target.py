'''
Copyright (c) 2011, Terrence Cole.
All rights reserved.
'''
from melano.project.lowlevel.function import LLFunction
import os.path


class Target:
	def __init__(self, bodyname, headername):
		# target files
		self.bodyname = bodyname
		self.headername = headername
		self.body = open(self.bodyname, 'w')
		self.hdr = open(self.headername, 'w')

		# lower-level structures
		self.includes = []
		self.functions = []


	def create_function(self, name, args=[], arg_tys=[], rty='void'):
		fn = LLFunction(name, args, arg_tys, rty)
		self.functions.append(fn)
		return fn


	def get_header_protect_token(self):
		base = os.path.basename(self.headername).upper()
		return '_' + base.replace('.', '_') + '_'


	def emit(self):
		hdrtoken = self.get_header_protect_token()
		self.hdr.write("#ifndef {0}\n#define {0}\n".format(hdrtoken))

		self.body.write('#include "{}"\n'.format(os.path.basename(self.headername)))

		for fn in self.functions:
			fn.emit_prototype(self.hdr, '')
			self.hdr.write('\n')

		for fn in self.functions:
			fn.emit(self.body, '')
			self.hdr.write('\n')

		self.hdr.write("#endif\n")


	def close(self):
		self.body.close()
		self.hdr.close()

