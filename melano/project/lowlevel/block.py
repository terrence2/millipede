'''
Copyright (c) 2011, Terrence Cole.
All rights reserved.
'''
from collections import OrderedDict
from melano.project.lowlevel.if_stmt import LLIf
import itertools



class LLBlock:
	'''Collection of statements in {}'''

	def __init__(self, target=None):
		self.target = target # the owning translation unit
		self.name_no = itertools.count()
		self.vars = OrderedDict() # {name: (typeattrs, typesig)} 
		self.stmts = []


	def is_name_in_scope(self, name):
		if name in self.vars: return True
		return self.target.is_name_in_scope(name)


	def get_variable_name(self, base):
		'''Create a new, unique identifier name, given the base name.  Will not choose a used identifier and
			this is not reverse-mappable to base.
		'''
		i = 0
		n = base
		while self.is_name_in_scope(n):
			n = base + str(i)
			i += 1
		return n


	def get_temp_name(self):
		return '_' + str(next(self.name_no))


	def import_python(self, module:str):
		name = self.get_variable_name(module.replace('.', '_'))
		self.add_variable('PyObject*', name)
		self.stmts.extend([
						'{} = PyImport_ImportModule("{}");'.format(name, module),
						'if(!{}) return NULL;'.format(name),
						])
		return name


	def import_from(self, level:int, module:str, names:[str]):
		pass


	def add_variable(self, ty, name, attrs=''):
		assert name not in self.vars
		self.vars[name] = (attrs, ty)


	"""
	def if_stmt(self):
		s = LLIf()
		self.stmts.append(s)
		return s


	def else_stmt(self):
		s = LLElse()
		self.stmts.append(s)
		return s


	def block(self):
		b = LLBlock()
		self.stmts.append(b)
		return b
	"""


	def emit(self, fp, pad):
		fp.write(pad + '{\n')
		for var, (tyattrs, tysig) in self.vars.items():
			if tyattrs: tysig = tyattrs + ' ' + tysig
			fp.write('\t' + pad + tysig + ' ' + var + ';\n')
		for stmt in self.stmts:
			# TODO: is this right?
			if isinstance(stmt, str):
				fp.write('\t' + pad + stmt + '\n')
			else:
				stmt.emit(fp, pad + '\t')
				fp.write('\n')
		fp.write(pad + '}\n')

