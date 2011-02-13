'''
Copyright (c) 2011, Terrence Cole.
All rights reserved.
'''
from . import ast as c
from contextlib import contextmanager
from melano.c.pybuiltins import PY_BUILTINS
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

		# the python walker context
		self.globals = None
		self.locals = None

		# the main unit where we put top-level entries
		self.translation_unit = c.TranslationUnit()
		self.translation_unit.add_include(c.Include('Python.h', True))
		self.translation_unit.add_fwddecl(c.Decl('builtins', self.PyObjectP('builtins')))

		# the main function -- handles init, cleanup, and error printing at top level
		self.main = c.FuncDef(
			c.Decl('main',
				c.FuncDecl(c.ParamList(
						c.Decl('argc', c.TypeDecl('argc', c.IdentifierType('int'))),
						c.Decl('argv', c.PtrDecl(c.PtrDecl(c.TypeDecl('argv', c.IdentifierType('char')))))),
					c.TypeDecl('main', c.IdentifierType('int')))
			),
			c.Compound(
					c.FuncCall(c.ID('Py_Initialize'), c.ExprList()),
					c.Assignment('=', c.ID('builtins'), c.FuncCall(c.ID('PyImport_ImportModule'), c.ExprList(c.Constant('string', 'builtins'))))
			)
		)
		self.translation_unit.add_fwddecl(self.main.decl)
		self.translation_unit.add(self.main)

		# keep all public names to ensure we don't alias
		self.namespaces = []
		self.tmp_offset = itertools.count()

	def close(self):
		self.main.add(c.FuncCall(c.ID('Py_Finalize'), c.ExprList()))
		self.main.add(c.Return(c.Constant('integer', 0)))

	@contextmanager
	def global_scope(self, ctx):
		prior = self.globals
		self.globals = ctx
		yield
		self.globals = prior

	@contextmanager
	def local_scope(self, ctx):
		prior = self.locals
		self.locals = ctx
		yield
		self.locals = prior

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


	def _error_if_null(self, name:str, cleanup:[str]=[], error=None) -> c.If:
		decls = [c.FuncCall(c.ID('Py_DECREF'), c.ExprList(c.ID(name))) for name in cleanup]
		decls.append(c.Return(c.ID('NULL')))
		return c.If(c.UnaryOp('!', c.ID(name)), c.Compound(*decls), None)

	def _error_if_nonzero(self, name:str, cleanup:[str]=[], error=None) -> c.If:
		decls = [c.FuncCall(c.ID('Py_DECREF'), c.ExprList(c.ID(name))) for name in cleanup]
		decls.append(c.Return(c.ID('NULL')))
		return c.If(c.BinaryOp('!=', c.Constant('integer', 0), c.ID(name)), c.Compound(*decls), None)


	def visit_Module(self, node):
		mod = node.hl
		modfunc = mod.owner.global_name
		modname = mod.owner.name + '_local'
		modglobal = mod.owner.global_name + '_mod'
		moddict = modname + '_dict'
		tmp0 = self.tmpname()
		tmp1 = self.tmpname()
		tmp2 = self.tmpname()

		# entry point that creates the module namespace
		self.entry = c.FuncDef(
			c.Decl(modfunc,
				c.FuncDecl(c.ParamList(), c.PtrDecl(c.TypeDecl(modfunc, c.IdentifierType('PyObject'))))),
			c.Compound()
		)
		self.translation_unit.add_fwddecl(self.entry.decl)
		self.translation_unit.add(self.entry)

		# fwddecl all variables we know we will need
		self.entry.add_variable(c.Decl(modname, self.PyObjectP(modname)))
		self.entry.add_variable(c.Decl(moddict, self.PyObjectP(moddict)))
		self.entry.add_variable(c.Decl('__name__', self.PyObjectP('__name__')))
		self.entry.add_variable(c.Decl('__file__', self.PyObjectP('__file__')))
		self.entry.add_variable(c.Decl(tmp0, c.TypeDecl(tmp0, c.IdentifierType('int'))))
		self.entry.add_variable(c.Decl(tmp1, c.TypeDecl(tmp1, c.IdentifierType('int'))))

		# create the module
		self.entry.add(c.Assignment('=', c.ID(modname), c.FuncCall(c.ID('PyModule_New'),
																c.ExprList(c.Constant('string', self.str2c(mod.owner.name))))))
		self.entry.add(self._error_if_null(modname))
		self.entry.cleanup.append(modname)

		# get module dict
		self.entry.add(c.Assignment('=', c.ID(moddict), c.FuncCall(c.ID('PyModule_GetDict'), c.ExprList(c.ID(modname)))))
		self.entry.add(self._error_if_null(moddict, self.entry.cleanup))

		# add the name
		self.entry.add(c.Assignment('=', c.ID('__name__'), c.FuncCall(c.ID('PyUnicode_FromString'),
															c.ExprList(c.Constant('string', self.str2c(mod.owner.name))))))
		self.entry.add(self._error_if_null('__name__', self.entry.cleanup))
		self.entry.cleanup.append('__name__')
		self.entry.add(c.Assignment('=', c.ID(tmp0), c.FuncCall(c.ID('PyDict_SetItemString'),
															c.ExprList(c.ID(moddict), c.Constant('string', '__name__'), c.ID('__name__')))))
		self.entry.add(self._error_if_nonzero(tmp0, self.entry.cleanup))

		# add the file
		self.entry.add(c.Assignment('=', c.ID('__file__'), c.FuncCall(c.ID('PyUnicode_FromString'),
															c.ExprList(c.Constant('string', self.str2c(mod.filename))))))
		self.entry.add(self._error_if_null('__file__', self.entry.cleanup))
		self.entry.cleanup.append('__file__')
		self.entry.add(c.Assignment('=', c.ID(tmp1), c.FuncCall(c.ID('PyDict_SetItemString'),
															c.ExprList(c.ID(moddict), c.Constant('string', '__file__'), c.ID('__file__')))))
		self.entry.add(self._error_if_nonzero(tmp1, self.entry.cleanup))

		# add the docstring
		docstring, body = self._get_docstring(node.body)
		if docstring and self.emit_docstrings:
			self.entry.add_variable(c.Decl('__doc__', self.PyObjectP('__doc__')))
			self.entry.add_variable(c.Decl(tmp2, c.TypeDecl(tmp2, c.IdentifierType('int'))))

			self.entry.add(c.Assignment('=', c.ID('__doc__'), c.FuncCall(c.ID('PyUnicode_FromString'), c.ExprList(c.Constant('string', self.str2c(docstring))))))
			self.entry.add(self._error_if_null('__doc__', self.entry.cleanup))
			self.entry.cleanup.append('__doc__')
			self.entry.add(c.Assignment('=', c.ID(tmp2), c.FuncCall(c.ID('PyDict_SetItemString'), c.ExprList(
											c.ID(moddict), c.Constant('string', '__doc__'), c.ID('__doc__')))))
			self.entry.add(self._error_if_nonzero(tmp2, self.entry.cleanup))

		with self.global_scope(mod):
			self.visit_nodelist(body)

		# return the module
		self.entry.cleanup.remove(modname)
		for name in self.entry.cleanup:
			self.entry.add(c.FuncCall(c.ID('Py_DECREF'), c.ExprList(c.ID(name))))
		self.entry.add(c.Return(c.ID(modname)))

		# add the function call to the main to set the module's global name
		self.translation_unit.add_variable(c.Decl(modglobal, self.PyObjectP(modname)))
		self.main.add(c.Assignment('=', c.ID(modglobal), c.FuncCall(c.ID(modfunc), c.ExprList())))
		self.main.add(c.If(c.UnaryOp('!', c.ID(modglobal)), c.Return(c.Constant('integer', 1)), None))


	def visit_Assign(self, node):
		val = self.visit(node.value)

		for target in node.targets:
			name = self.visit(target)
			self.entry.add(c.Assignment('=', c.ID(name), c.ID(val)))
			self.entry.add(c.FuncCall(c.ID('Py_INCREF'), c.ExprList(c.ID(name))))
			self.entry.cleanup.append(name)


	def visit_FunctionDef(self, node):
		'''
		self.visit(node.returns) # return annotation
		self.visit_nodelist_field(node.args.args, 'annotation') # position arg annotations
		self.visit(node.args.varargannotation) # *args annotation
		self.visit_nodelist_field(node.args.kwonlyargs, 'annotation') # kwargs annotation
		self.visit(node.args.kwargannotation) # **args annotation
		self.visit_nodelist(node.args.defaults) # positional arg default values
		self.visit_nodelist(node.args.kw_defaults) # kwargs default values

		with self.scope(node):
			# arg name defs are inside the func
			self.visit_nodelist_field(node.args.args, 'arg')
			self.visit(node.args.vararg)
			self.visit_nodelist_field(node.args.kwonlyargs, 'arg')
			self.visit(node.args.kwarg)

			self.visit_nodelist(node.body)

		self.visit_nodelist(node.decorator_list)
		'''
		funcname = node.name.hl.global_name
		funcname_local = node.name.hl.ll_name + '_py'

		prior = self.entry

		# entry point that creates the module namespace
		self.entry = c.FuncDef(
			c.Decl(funcname,
				c.FuncDecl(c.ParamList(c.Decl('self', self.PyObjectP('self')), c.Decl('args', self.PyObjectP('args'))), \
						c.PtrDecl(c.TypeDecl(funcname, c.IdentifierType('PyObject'))))),
			c.Compound()
		)
		self.translation_unit.add_fwddecl(self.entry.decl)
		self.translation_unit.add(self.entry)

		# query the docstring -- we actually want to declare it once in the module, but need to get the real bodylist here
		docstring, body = self._get_docstring(node.body)

		with self.local_scope(node.hl.scope):
			self.visit_nodelist(body)


		#funcname = self.visit(node.name)
		#hl = self.context.symbols[str(node.name)]

		# reset our context and add declaration there
		self.entry = prior
		self.entry.add_variable(c.Decl(funcname_local, self.PyObjectP(funcname_local)))

		# wrap the function in a PyCFunction
		#TODO: keyword functions and other call types
		mdef = self.tmpname()
		self.entry.add_variable(c.Decl(mdef, c.Struct('PyMethodDef')))
		self.entry.add(c.Assignment('=', c.ID(mdef), c.Struct('PyMethodDef',
								c.Constant('string', str(node.name)), c.ID(funcname), c.ID('METH_VARARGS'), c.ID('NULL'))))

		# add the docstring
		if docstring and self.emit_docstrings:
			tmp2 = self.tmpname()
			self.entry.add_variable(c.Decl('__doc__', self.PyObjectP('__doc__')))
			self.entry.add_variable(c.Decl(tmp2, c.TypeDecl(tmp2, c.IdentifierType('int'))))

			self.entry.add(c.Assignment('=', c.ID('__doc__'), c.FuncCall(c.ID('PyUnicode_FromString'), c.ExprList(c.Constant('string', self.str2c(docstring))))))
			self.entry.add(self._error_if_null('__doc__', self.entry.cleanup))
			self.entry.cleanup.append('__doc__')
			self.entry.add(c.Assignment('=', c.ID(tmp2), c.FuncCall(c.ID('PyDict_SetItemString'), c.ExprList(
											c.ID(moddict), c.Constant('string', '__doc__'), c.ID('__doc__')))))
			self.entry.add(self._error_if_nonzero(tmp2, self.entry.cleanup))

		return funcname



	def visit_Name(self, node):
		if node.ctx == py.Store:
			#TODO: global and nonlocal storage
			if self.locals:
				try:
					sym = self.locals.lookup(str(node))
				except KeyError:
					pass
			if not sym:
				sym = self.globals.lookup(str(node))
			self.entry.add_variable(c.Decl(sym.ll_name, self.PyObjectP(sym.ll_name)))
			return sym.ll_name
		elif node.ctx == py.Load:
			# try local namespace
			if self.locals:
				try:
					sym = self.locals.lookup(str(node))
					return sym.ll_name
				except KeyError:
					pass
			# try the global namespace
			try:
				sym = self.globals.lookup(str(node))
				if not self.locals:
					return sym.ll_name
			except KeyError:
				pass
			# import from the builtins namespace
			if str(node) in PY_BUILTINS:
				n = self.tmpname()
				self.entry.add_variable(c.Decl(n, self.PyObjectP(n)))
				self.entry.add(c.Assignment('=', c.ID(n), c.FuncCall(c.ID('PyObject_GetAttrString'),
																		c.ExprList(c.ID('builtins'), c.Constant('string', str(node))))))
				self.entry.add(self._error_if_null(n, self.entry.cleanup))
				self.entry.cleanup.append(n)
				return n


	def visit_Num(self, node):
		tmp = self.tmpname()
		self.entry.add_variable(c.Decl(tmp, self.PyObjectP(tmp)))
		if isinstance(node.n, int):
			if node.n < 2 ** 63 - 1:
				self.entry.add(c.Assignment('=', c.ID(tmp), c.FuncCall(c.ID('PyLong_FromLong'), c.ExprList(c.Constant('integer', node.n)))))
			else:
				self.entry.add(c.Assignment('=', c.ID(tmp), c.FuncCall(c.ID('PyLong_FromString'), c.ExprList(
																			c.Constant('string', str(node.n)), c.ID('NULL'), c.Constant('integer', 0)))))
		self.entry.add(self._error_if_null(tmp, self.entry.cleanup))
		self.entry.cleanup.append(tmp)

		return tmp


	def visit_Return(self, node):
		name = self.visit(node.value)
		self.entry.cleanup.remove(name)
		for n in self.entry.cleanup:
			self.entry.add(c.FuncCall(c.ID('Py_DECREF'), c.ExprList(c.ID(n))))
		self.entry.add(c.Return(c.ID(name)))


	def visit_Str(self, node):
		tmp = self.tmpname()
		self.entry.add_variable(c.Decl(tmp, self.PyObjectP(tmp)))
		self.entry.add(c.Assignment('=', c.ID(tmp), c.FuncCall(c.ID('PyUnicode_FromString'), c.ExprList(c.Constant('string', self.str2c(node.s))))))
		self.entry.add(self._error_if_null(tmp, self.entry.cleanup))
		self.entry.cleanup.append(tmp)
		return tmp



	"""

	def visit_Attribute(self, node):
		if node.ctx == ast.Store:
			varname = self.context.get_variable_name(str(node).replace('.', '_'))
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
