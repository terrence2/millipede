'''
Copyright (c) 2011, Terrence Cole.
All rights reserved.
'''
from collections import OrderedDict
from melano.project.lowlevel.function import LLFunction, LLModuleFunction
import os.path


class Target:
	def __init__(self, basename, bodyname, headername):
		self.basename = basename

		# target files
		self.bodyname = bodyname
		self.headername = headername
		self.body = open(self.bodyname, 'w')
		self.hdr = open(self.headername, 'w')

		# lower-level structures
		self.includes = []
		self.globals = OrderedDict() # {name: (typeattrs, typesig)}
		self.functions = OrderedDict() # {name: LLFunction()}


	def name(self):
		return self.basename


	def is_name_in_scope(self, name):
		'''FIXME: this needs to look also at imported variables.'''
		return name in self.globals or name in self.functions


	def add_global(self, ty:str, name:str):
		'''Expose the given name as a static global.'''
		self.globals[name] = ('static', ty)


	def create_module_function(self):
		name = self.name()
		fn = LLModuleFunction(name, target=self)
		self.functions[name] = fn
		return fn


	def create_function(self, name, args=[], arg_tys=[], rty='PyObject*'):
		name = self.name() + '_' + name
		fn = LLFunction(name, args, arg_tys, rty, target=self)
		self.functions[name] = fn
		return fn


	def get_header_protect_token(self):
		base = os.path.basename(self.headername).upper()
		return '_' + base.replace('.', '_') + '_'


	def emit(self):
		hdrtoken = self.get_header_protect_token()
		self.hdr.write("#ifndef {0}\n#define {0}\n".format(hdrtoken))

		self.body.write('#include "{}"\n'.format(os.path.basename(self.headername)))

		for fn in self.functions.values():
			fn.emit_prototype(self.hdr, '')
			self.hdr.write('\n')

		for fn in self.functions.values():
			fn.emit(self.body, '')
			self.hdr.write('\n')

		self.hdr.write("#endif\n")


	def close(self):
		self.body.close()
		self.hdr.close()


class EntryPoint(Target):
	def __init__(self, program, basename, bodyname, headername):
		super().__init__(basename, bodyname, headername)
		self.entry = None


	def set_entry(self, entry):
		self.entry = entry


	def emit(self):
		self.body.write('#include <Python.h>\n')
		super().emit()
		self.body.write("""
int main(int argc, char **argv) {{
	Py_Initialize();
	PySys_SetArgv(argc, argv);
	{}();
	Py_Finalize();
	return 0;
}}
""".format(self.entry))



