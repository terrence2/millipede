'''
Copyright (c) 2011, Terrence Cole.
All rights reserved.
'''
from . import ast as c
from contextlib import contextmanager
from melano.parser import ast as py
from melano.parser.visitor import ASTVisitor
import itertools



class Py2C(ASTVisitor):
	'''
	Use the type information to lay out low-level code (or high-level code as needed).
	'''
	def __init__(self, *, docstrings=True):
		super().__init__()

		# options
		self.emit_docstrings = docstrings

		# the main unit where we put top-level entries
		self.translation_unit = c.TranslationUnit()
		imp = c.Include('Python.h', True)
		self.translation_unit.ext.insert(0, imp)

		# entry point that creates the module namespace
		self.entry = c.FuncDef(
			c.Decl('entryfunc',
				c.FuncDecl(c.ParamList(), c.PtrDecl(c.TypeDecl('entryfunc', c.IdentifierType('PyObject'))))),
			c.Compound()
		)
		self.translation_unit.ext.append(self.entry)

		# the main function -- handles init, cleanup, and error printing at top level
		# int main(int argc, char** argv) {
		#		Py_Initialize();
		#		entryfunc();
		#		Py_Terminate();
		# }
		self.main = c.FuncDef(
			c.Decl('main',
				c.FuncDecl(c.ParamList(
						c.Decl('argc', c.TypeDecl('argc', c.IdentifierType('int'))),
						c.Decl('argv', c.PtrDecl(c.PtrDecl(c.TypeDecl('argv', c.IdentifierType('char')))))),
					c.TypeDecl('main', c.IdentifierType('int')))
			),
			c.Compound(
					c.Decl('rv', c.PtrDecl(c.TypeDecl('rv', c.IdentifierType('PyObject')))),
					c.FuncCall(c.ID('Py_Initialize'), c.ExprList()),
					c.Assignment('=', c.ID('rv'), c.FuncCall(c.ID('entryfunc'), c.ExprList())),
					c.If(c.UnaryOp('!', c.ID('rv')), c.Compound(
							c.FuncCall(c.ID('PyErr_Print'), c.ExprList()),
							c.Return(c.Constant('integer', 1))
						), None),
					c.FuncCall(c.ID('Py_Finalize'), c.ExprList()),
					c.Return(c.Constant('integer', 0))
			)
		)
		self.translation_unit.ext.append(self.main)

		# keep all public names to ensure we don't alias
		self.namespaces = []
		self.tmp_offset = itertools.count()

	def close(self):
		self.entry.body.block_items.append(c.ID('Py_RETURN_NONE'))

	def tmpname(self):
		'''Return a unique temporary variable name'''
		return 'tmp' + str(next(self.tmp_offset))

	def str2c(self, value):
		return value.replace('\n', '\\n').strip("'").strip('"')

	def PyObjectP(self, name):
		return c.PtrDecl(c.TypeDecl(name, c.IdentifierType('PyObject')))

	def _get_docstring(self, nodes):
		if nodes and isinstance(nodes[0], py.Expr) and isinstance(nodes[0].value, py.Str):
			return nodes[0].value.s, nodes[1:]
		return None, nodes

	def visit_Module(self, node):
		# /* module for <filename> */
		# PyObject *<name> = PyModule_New("<name>");
		# if(!<name>) return NULL;
		name = node.hl.name
		self.entry.add_variable(c.Decl(name, self.PyObjectP(name)))
		self.entry.add(c.Comment('module for ' + node.hl.filename))
		self.entry.add(c.Assignment('=', c.ID(name), c.FuncCall(c.ID('PyModule_New'), c.ExprList(c.Constant('string', name)))))
		self.entry.add(c.If(c.UnaryOp('!', c.ID(name)), c.Return(c.ID('NULL')), None))

		self.namespaces.append(name)

		# try to add a doc string, if present
		docstring, body = self._get_docstring(node.body)
		if docstring and self.emit_docstrings:
			#/* docstring for module <name> */
			#PyObject *<tmp0> = PyUnicode_FromString(<docstring>);
			#if(!<tmp0>) return NULL;
			#PyObject *<tmp1> = PyModule_GetDict(<name>); // borrowed ref
			#if(!<tmp1>) return NULL;
			#PyDict_SetItemString(<tmp1>, "__doc__", <tmp0>);
			self.entry.add(c.Comment('docstring for module ' + name))
			tmp0 = self.tmpname()
			self.entry.add_variable(c.Decl(tmp0, self.PyObjectP(tmp0)))
			self.entry.add(c.Assignment('=', c.ID(tmp0), c.FuncCall(c.ID('PyUnicode_FromString'), c.ExprList(c.Constant('string', self.str2c(docstring))))))
			self.entry.add(c.If(c.UnaryOp('!', c.ID(tmp0)), c.Return(c.ID('NULL')), None))
			tmp1 = self.tmpname()
			self.entry.add_variable(c.Decl(tmp1, self.PyObjectP(tmp1)))
			self.entry.add(c.Assignment('=', c.ID(tmp1), c.FuncCall(c.ID('PyModule_GetDict'), c.ExprList(c.ID(name)))))
			self.entry.add(c.If(c.UnaryOp('!', c.ID(tmp1)), c.Return(c.ID('NULL')), None))
			tmp2 = self.tmpname()
			self.entry.add_variable(c.Decl(tmp2, c.TypeDecl(tmp2, c.IdentifierType('int'))))
			self.entry.add(c.Assignment('=', c.ID(tmp2), c.FuncCall(c.ID('PyDict_SetItemString'), c.ExprList(
											c.ID(tmp1), c.Constant('string', '__doc__'), c.ID(tmp0)))))
			self.entry.add(c.If(c.BinaryOp('!=', c.Constant('integer', 0), c.ID(tmp2)), c.Return(c.ID('NULL')), None))

		# visit rest of body
		self.visit_nodelist(body)



	"""

	def visit_Attribute(self, node):
		if node.ctx == ast.Store:
			varname = self.context.get_variable_name(str(node).replace('.', '_'))
			self.context.add_variable(node.hl.get_type().name(), varname)
			node.hl.name = varname


	def visit_Name(self, node):
		if node.ctx == ast.Store:
			varname = self.context.get_variable_name(node.id)
			self.context.add_variable(node.hl.get_type().name(), varname)
			node.hl.name = varname


	def visit_FunctionDef(self, node):
		ctx = self.target.create_function(str(node.name))
		with self.scope(ctx):
			self.visit_nodelist(node.body)


	def visit_Import(self, node):
		for alias in node.names:
			self.visit(alias.name)
			self.visit(alias.asname)
			return

			# Note: exposing a name can take one of two paths, either importing an existing LL definition from another
			#		LL source, making it directly available, or we need to perform a pythonic import to get the names
			mod = self.project.find_module(str(alias.name), self.module)
			if self.project.is_local(mod):
				raise NotImplementedError
				self.target.import_local(str(alias.name))
			else:
				#self.context.import_python(str(alias.name))
				print('IMP:', alias.name.hl.name)

	"""

	"""

	#def visit_ImportFrom(self, node):
	#	#import pdb;pdb.set_trace()
	#	self.context.import_from(node.level, str(node.module), [str(n) for n in node.names])


	def visit_If(self, node):
		self.visit(node.test)
		print(node.test.hl.name)
		#ctx = self.context.create_if():
		#with self.scope(ctx):
		#	self.visit_nodelist(nodes)


	def visit_Compare(self, node):
		self.visit(node.left)


	def visit_Attribute(self, node):
		self.visit(node.value)


	def visit_Assign(self, node):
		for tgt in node.targets:
			self.context.add_variable(tgt.hl.type(), str(tgt))
		import pdb; pdb.set_trace()


	def visit_If(self, node):
		with self.scope(self.context.if_stmt()):
			self.visit(node.test)
		with self.scope(self.context.block()):
			self.visit_nodelist(node.body)
		if node.orelse:
			self.context.else_stmt()
			with self.scope(self.context.block()):
				self.visit_nodelist(node.orelse)
	"""
