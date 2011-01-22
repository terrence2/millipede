'''
Copyright (c) 2011, Terrence Cole.
All rights reserved.
'''
from melano.project.lowlevel.target import Target


class Entrypoint(Target):
	def __init__(self, program, bodyname, headername):
		super().__init__(bodyname, headername)
		self.entry = None


	def set_entry(self, entry):
		self.entry = entry


	def emit(self):
		self.body.write('#include <Python.h>\n')
		super().emit()
		self.body.write("""
int main(int argc, char **argv) {{
	Py_Initialize();
	{}();
	return 0;
}}
""".format(self.entry))


