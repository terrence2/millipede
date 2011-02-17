'''
Copyright (c) 2011, Terrence Cole.
All rights reserved.
'''
from . import ast as c
from contextlib import contextmanager
from melano.c.pybuiltins import PY_BUILTINS
from melano.c.types.pyobject import PyObjectType
from melano.c.types.pystring import PyStringType
from melano.parser import ast as py
from melano.parser.visitor import ASTVisitor
import itertools
import pdb
import tc



class Py2C(ASTVisitor):
	'''
	Use the type information to lay out low-level code (or high-level code as needed).
	'''
	def __init__(self, *, docstrings=True):
		super().__init__()

		# options
		self.opt_emit_docstrings = docstrings
		self.opt_static_globals = False

		# the python walker context
		self.globals = None
		self.locals = None

		# the main unit where we put top-level entries
		self.tu = c.TranslationUnit()

		# add includes
		self.tu.add_include(c.Include('Python.h', True))
		self.tu.add_include(c.Include('data/c/env.h', False))

		# add common names
		self.tu.reserve_name('builtins', None)
		self.tu.reserve_name('None', None)
		self.tu.add_fwddecl(c.Decl('builtins', c.PtrDecl(c.TypeDecl('builtins', c.IdentifierType('PyObject'))), ['static']))
		self.tu.add_fwddecl(c.Decl('None', c.PtrDecl(c.TypeDecl('None', c.IdentifierType('PyObject'))), ['static']))

		# the main function -- handles init, cleanup, and error printing at top level
		self.tu.reserve_name('main', None)
		self.main = c.FuncDef(
			c.Decl('main',
				c.FuncDecl(c.ParamList(
						c.Decl('argc', c.TypeDecl('argc', c.IdentifierType('int'))),
						c.Decl('argv', c.PtrDecl(c.PtrDecl(c.TypeDecl('argv', c.IdentifierType('char')))))),
					c.TypeDecl('main', c.IdentifierType('int')))
			),
			c.Compound(
					c.FuncCall(c.ID('assert'), c.ExprList(c.BinaryOp('==', c.FuncCall(c.ID('sizeof'), c.ExprList(c.ID('Py_UNICODE'))), c.Constant('integer', 4)))),
					c.FuncCall(c.ID('Py_Initialize'), c.ExprList()),
					c.Assignment('=', c.ID('builtins'), c.FuncCall(c.ID('PyImport_ImportModule'), c.ExprList(c.Constant('string', 'builtins')))),
					c.Assignment('=', c.ID('None'), c.FuncCall(c.ID('PyObject_GetAttrString'), c.ExprList(c.ID('builtins'), c.Constant('string', 'None')))),
			)
		)
		self.tu.add_fwddecl(self.main.decl)
		self.tu.add(self.main)

		# ensure tmp vars never alias
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


	"""
	def tmpname(self):
		'''Return a unique temporary variable name'''
		n = self.func.reserve_name('tmp' + str(next(self.tmp_offset)), None, self.tu)
		return n

	def str2c(self, value:str) -> str:
		'''Reformats a python string to make it suitable for use as a C string constant.'''
		return value.replace('\n', '\\n').strip("'").strip('"')

	def PyObjectP(self, name):
		return c.PtrDecl(c.TypeDecl(name, c.IdentifierType('PyObject')))
	"""

	def split_docstring(self, nodes:[py.AST]) -> (tc.Nonable(str), [py.AST]):
		'''Given the body, will pull off the docstring node and return it and the rest of the body.'''
		if nodes and isinstance(nodes[0], py.Expr) and isinstance(nodes[0].value, py.Str):
			if not self.opt_emit_docstring:
				return None, nodes[1:]
			return nodes[0].value.s, nodes[1:]
		return None, nodes


	"""
	def _error_if_null(self, name:str, cleanup:[str]=[], error=None) -> c.If:
		decls = [c.FuncCall(c.ID('Py_DECREF'), c.ExprList(c.ID(name))) for name in cleanup]
		decls.append(c.Return(c.ID('NULL')))
		return c.If(c.FuncCall(c.ID('unlikely'), c.ExprList(c.UnaryOp('!', c.ID(name)))), c.Compound(*decls), None)

	def _error_if_nonzero(self, name:str, cleanup:[str]=[], error=None) -> c.If:
		decls = [c.FuncCall(c.ID('Py_DECREF'), c.ExprList(c.ID(name))) for name in cleanup]
		decls.append(c.Return(c.ID('NULL')))
		return c.If(c.FuncCall(c.ID('unlikely'), c.ExprList(c.BinaryOp('!=', c.Constant('integer', 0), c.ID(name)))), c.Compound(*decls), None)
	"""


	def _assign(self, target, value):
		'''
		All of our nodes that add a name (e.g. Assign, FunctionDef, Import, etc), need to have the same logic.
		'''
		# if the lhs is an attribute; (only for assign)
		# if we are at global scope globals (have no locals);
		# if we have a potential closure user; (no closure = no nonlocal access)
		# ---> we need to attach the value to the underlying object for out-of-(c)-scope references
		tgt_obj, tgt_name = None, None
		if isinstance(target, py.Attribute):
			sym = target.value.hl
			if not sym:
				sym = self.lookup_symbol(str(target))
			tgt_obj = target.value.hl.ll_name
			tgt_name = target.attr.hl.name
		elif not self.locals:
			assert isinstance(target, py.Name) and target.ctx == py.Store
			tgt_obj = self.globals.owner.global_name + '_mod'
			tgt_name = str(target)
		elif self.locals.has_closure():
			assert isinstance(target, py.Name) and target.ctx == py.Store
			tgt_obj = self.locals.owner.global_name + '_func'
			tgt_name = str(target)

		if tgt_obj and tgt_name:
			tmp = self.tmpname()
			self.func.add_variable(c.Decl(tmp, c.TypeDecl(tmp, c.IdentifierType('int'))))
			self.func.add(c.Assignment('=', c.ID(tmp), c.FuncCall(c.ID('PyObject_SetAttrString'), c.ExprList(
															c.ID(tgt_obj), c.Constant('string', str(tgt_name)), c.ID(value)))))
			self.func.add(self._error_if_nonzero(tmp, self.func.cleanup))


	def visit_Module(self, node):
		# get the MelanoModule and Name
		modscope = node.hl
		modname = modscope.owner

		# modules need 3 global names:
		#		1) the module itself (modname.global_name)
		#		2) the module's scope dict (modscope.ll_scope)
		#		3) the module builder function (modscope.ll_builder)
		modname.global_name = self.tu.reserve_name(modname.global_name, modname)
		modscope.ll_scope = self.tu.reserve_name(modname.global_name + '_dict', modscope)
		modscope.ll_builder = self.tu.reserve_name(modname.global_name + '_builder', modscope)

		# create the module creation function
		self.module_func = self.func = c.FuncDef(
			c.Decl(modscope.ll_builder,
				c.FuncDecl(
						c.ParamList(),
						c.PtrDecl(c.TypeDecl(modscope.ll_builder, c.IdentifierType('PyObject'))))),
			c.Compound()
		)
		self.tu.add_fwddecl(self.func.decl)
		self.tu.add(self.func)

		# create the module
		modname.create_instance(modname.global_name)
		modname.inst.declare(self.tu, ['static'])
		modname.inst.new(self.func, modname.name)

		# load the module dict from the module to the scope
		modscope.create_instance(modscope.ll_scope)
		modscope.inst.declare(self.tu, ['static'])
		modname.inst.get_dict(modscope.ll_scope, self.func)

		# load and attach special attributes to the module dict
		docstring, body = self.split_docstring(node.body)
		for name, s in [('__name__', modname.name), ('__file__', modscope.filename), ('__doc__', docstring)]:
			if s is not None:
				ps = PyStringType(self.func.reserve_name(name, None, self.tu))
				ps.new(self.func, s)
			else:
				ps = PyObjectType(self.func.reserve_name(name, None, self.tu))
				ps.set_none(self.func)
			ps.declare(self.func) # note: this can come after we use the name, it just has to happen
			modscope.inst.set_item(self.func, name, ps.name)

		# visit all children
		with self.global_scope(modscope):
			self.visit_nodelist(body)

		# return the module
		self.func.cleanup.remove(modname.global_name)
		for name in reversed(self.func.cleanup):
			self.func.add(c.FuncCall(c.ID('Py_DECREF'), c.ExprList(c.ID(name))))
		self.func.add(c.Return(c.ID(modname.global_name)))

		# add the function call to the main to set the module's global name
		tmp = self.main.reserve_name(self.tmpname(), modname, self.tu)
		self.main.add_variable(c.Decl(tmp, self.PyObjectP(tmp)))
		self.main.add(c.Assignment('=', c.ID(tmp), c.FuncCall(c.ID(modscope.ll_builder), c.ExprList())))
		self.main.add(c.If(c.UnaryOp('!', c.ID(tmp)), c.Compound(
								c.FuncCall(c.ID('PyErr_Print'), c.ExprList()),
								c.Return(c.Constant('integer', 1),
							)), None))


	def visit_Assign(self, node):
		value = self.visit(node.value)

		for target in node.targets:
			name = self.visit(target)

			# create fast local reference
			self.func.add(c.Assignment(' = ', c.ID(name), c.ID(value)))
			self.func.add(c.FuncCall(c.ID('Py_INCREF'), c.ExprList(c.ID(name))))
			self.func.cleanup.append(name)

			self._assign(target, value)


	def visit_Attribute(self, node):
		lhs = self.visit(node.value)
		rhs = self.visit(node.attr)

		# attributes _also_ get an aggregate name in the local scope for fast usage in the same scope
		if not self.func.has_name(node.hl.ll_name):
			node.hl.ll_name = self.func.reserve_name(node.hl.ll_name, node.hl, self.tu)
			self.func.add_variable(c.Decl(node.hl.ll_name, self.PyObjectP(node.hl.ll_name)))
		return node.hl.ll_name

		"""
		# pick a good name for ourself, if we have one
		node.hl.ll_name
		if not self.func.has_name(name):
			name = node.hl.ll_name = self.func.reserve_name(name,
		name = self.func.reserve_name(name, node.hl, self.tu)
		self.func.add_variable(c.Decl(name, self.PyObjectP(name)))

		# short circuit the Name dereference and use GetAttrString here
		assert isinstance(node.attr, py.Name)
		self.func.add(c.Assignment(' = ', c.ID(name), c.FuncCall(c.ID('PyObject_GetAttrString'), c.ExprList(c.ID(lhs), c.Constant('string', node.attr.id)))))
		self.func.add(self._error_if_null(name, self.func.cleanup))
		self.func.cleanup.append(name)
		return name
		"""


	def visit_Call(self, node):
		#TODO: direct calling, keywords calling, etc
		#TODO: track "type" so we can dispatch to PyCFunction_Call or PyFunction_Call instead of PyObject_Call 
		#TODO: track all call methods (callsite usage types) and see if we can't unpack into a direct c call

		# get id of func
		funcname = self.visit(node.func)

		# get id of positional args
		id_of_args = []
		if node.args:
			for arg in node.args:
				id = self.visit(arg)
				id_of_args.append(id)

		# build a tuple with our positional args	
		#NOTE: Pack increfs the args, so we only need to delete the tuple later
		args = funcname + '_args'
		self.func.add_variable(c.Decl(args, self.PyObjectP(args)))
		to_pack = [c.ID(n) for n in id_of_args]
		self.func.add(c.Assignment('=', c.ID(args), c.FuncCall(c.ID('PyTuple_Pack'), c.ExprList(c.Constant('integer', len(id_of_args)), *to_pack))))
		self.func.add(self._error_if_null(args, self.func.cleanup))
		self.func.cleanup.append(args)

		# make the call
		rv = funcname + '_rv'
		self.func.add_variable(c.Decl(rv, self.PyObjectP(rv)))
		self.func.add(c.Assignment('=', c.ID(rv), c.FuncCall(c.ID('PyObject_Call'), c.ExprList(c.ID(funcname), c.ID(args), c.ID('NULL')))))
		self.func.add(self._error_if_null(rv, self.func.cleanup))
		self.func.cleanup.append(rv)

		# cleanup the call tuple
		self.func.add(c.FuncCall(c.ID('Py_DECREF'), c.ID(args)))
		self.func.cleanup.remove(args)


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
		funcname = node.name.hl.global_name = self.tu.reserve_name(node.name.hl.global_name, node.name.hl)
		funcname_local_def = self.func.reserve_name(funcname + '_def', None, self.tu)

		prior = self.func

		# entry point that creates the module namespace
		self.func = c.FuncDef(
			c.Decl(funcname,
				c.FuncDecl(c.ParamList(c.Decl('self', self.PyObjectP('self')), c.Decl('args', self.PyObjectP('args'))), \
						c.PtrDecl(c.TypeDecl(funcname, c.IdentifierType('PyObject'))))),
			c.Compound()
		)
		self.tu.add_fwddecl(self.func.decl)
		self.tu.add(self.func)

		# query the docstring -- we actually want to declare it once in the module, but need to get the real bodylist here
		docstring, body = self.split_docstring(node.body)

		with self.local_scope(node.hl.scope):
			self.visit_nodelist(body)

		# reset our context and add declaration there
		self.func = prior

		#TODO: keyword functions and other call types

		# wrap the function in a PyCFunction
		self.func.add_variable(c.Decl(funcname_local_def, c.TypeDecl(funcname_local_def, c.Struct('PyMethodDef')),
									init=c.ExprList(c.Constant('string', str(node.name)), c.ID(funcname), c.ID('METH_VARARGS'), c.ID('NULL'))))

		# add the function node to the namespace
		funcname_local = self.visit(node.name)
		#funcname_local = node.name.hl.ll_name = self.func.reserve_name(node.name.hl.ll_name, node.name.hl, self.tu)

		#self.func.add_variable(c.Decl(funcname_local, self.PyObjectP(funcname_local)))
		#self.func.add(c.Assignment('=', c.ID(funcname_local), c.FuncCall(c.ID('PyCFunction_NewEx'), c.ExprList(
		#														c.UnaryOp('&', c.ID(funcname_local_def)), c.ID(self_name), c.ID(mod_name)))))
		#FIXME: class needs self as instance object? what about just functions?
		self.func.add(c.Assignment('=', c.ID(funcname_local), c.FuncCall(c.ID('PyCFunction_NewEx'), c.ExprList(
																c.UnaryOp('&', c.ID(funcname_local_def)), c.ID(self.globals.owner.ll_name + '_mod'), c.ID('__name__')))))
		self.func.add(self._error_if_null(funcname_local, self.func.cleanup))
		self.func.cleanup.append(funcname_local)
		self._assign(node.name, funcname_local)

		"""
		# create the function
		self_name = 'self' if self.locals else 'NULL'
		mod_name = self.globals.owner.name + '_mod'
		
		# add the function to the surrounding namespace
		#self._attach_name(str(node.name), funcname_local)
		"""

		# add the docstring
		#FIXME: we need to load all docstring (and other func attributes) in the module scope to avoid repeating ourselves every call
		#if docstring and self.emit_docstrings:
		#	tmp2 = self.tmpname()
		#	self.func.add_variable(c.Decl('__doc__', self.PyObjectP('__doc__')))
		#	self.func.add_variable(c.Decl(tmp2, c.TypeDecl(tmp2, c.IdentifierType('int'))))
		#
		#	self.func.add(c.Assignment('=', c.ID('__doc__'), c.FuncCall(c.ID('PyUnicode_FromString'), c.ExprList(c.Constant('string', self.str2c(docstring))))))
		#	self.func.add(self._error_if_null('__doc__', self.func.cleanup))
		#	self.func.cleanup.append('__doc__')
		#	self.func.add(c.Assignment('=', c.ID(tmp2), c.FuncCall(c.ID('PyDict_SetItemString'), c.ExprList(
		#									c.ID(moddict), c.Constant('string', '__doc__'), c.ID('__doc__')))))
		#	self.func.add(self._error_if_nonzero(tmp2, self.func.cleanup))

		return funcname



	def visit_Name(self, node):
		if node.ctx == py.Store:
			if not self.func.has_symbol(node.hl):
				node.hl.ll_name = self.func.reserve_name(node.hl.ll_name, node.hl, self.tu)
				self.func.add_variable(c.Decl(node.hl.ll_name, self.PyObjectP(node.hl.ll_name)))
			return node.hl.ll_name
		elif node.ctx == py.Load:
			if self.func.has_symbol(node.hl):
				return node.hl.ll_name
			else:
				# if the symbol is out of c scope, we need to fall back to loading it from the python scope
				#NOTE: normally we want to access the globals and then fall back to builtins; however, if we
				#		know that the access is for a builtin, we can skip globals unless there is something in the
				#		globals
				name = node.hl.name
				if name in PY_BUILTINS and name not in self.globals.symbols:
					tmp = self.tmpname()
					self.func.add_variable(c.Decl(tmp, self.PyObjectP(tmp)))
					self.func.add(c.Assignment('=', c.ID(tmp),
							c.FuncCall(c.ID('PyObject_GetAttrString'), c.ExprList(c.ID('builtins'), c.Constant('string', name)))))

				#TODO: we could potentially skip lookups in locals/globals if the name is for a builtin, 
				#		if can we detect/track when builtins get masked
				'''
				PyObject *tmp;
				...
				tmp = PyObject_GetAttrString(ID(locals.owner.ll_name), ID(node.hl.name));
				if(!tmp) {
					tmp = PyObject_GetAttrString(ID(self.globals.owner.ll_name), ID(node.hl.name));
					if(!tmp) {
						tmp = PyObject_GetAttrString(ID('builtins'), ID(node.hl.name));
						if(!tmp) {
							...
							return NULL;
						}
					}
				}
				...
				Py_DECREF(tmp);
				'''
				tmp = self.tmpname()
				self.func.add_variable(c.Decl(tmp, self.PyObjectP(tmp)))
				globals_lookup = c.Assignment('=', c.ID(tmp), c.FuncCall(c.ID('PyObject_GetAttrString'), c.ExprList(
							c.ID(self.globals.owner.ll_name + '_mod'), c.Constant('string', node.hl.name))))
				noglobal = c.Compound(
						c.Assignment('=', c.ID(tmp),
									c.FuncCall(c.ID('PyObject_GetAttrString'), c.ExprList(c.ID('builtins'), c.Constant('string', node.hl.name)))))
				noglobal.block_items.append(self._error_if_null(tmp, self.func.cleanup))
				noglobal = c.If(c.UnaryOp('!', c.ID(tmp)), noglobal, None)
				if self.locals:
					self.func.add(c.Assignment('=', c.ID(tmp), c.FuncCall(c.ID('PyObject_GetAttrString'), c.ExprList(
							c.ID('self'), c.Constant('string', node.hl.name)))))
					self.func.add(c.If(c.UnaryOp('!', c.ID(tmp)), c.Compound(globals_lookup, noglobal), None))
				else:
					self.func.add(globals_lookup)
					self.func.add(noglobal)
				return tmp

				#PyObject_GetAttrString(
				src_obj, src_name = None, None
				pdb.set_trace()
				#self.func.add(c. 


		"""
		if node.ctx == py.Store:
			#TODO: global and nonlocal storage
			sym = None
			if self.locals:
				try:
					sym = self.locals.lookup(str(node))
				except KeyError:
					pass
			if not sym:
				sym = self.globals.lookup(str(node))
			sym.ll_name = self.func.reserve_name(sym.ll_name, sym, self.tu)
			self.func.add_variable(c.Decl(sym.ll_name, self.PyObjectP(sym.ll_name)))
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
				# If we are at the module level (no locals), then our globals are available directly
				if not self.locals:
					return sym.ll_name
				# otherwise, we need to load the name manually off the module
				else:
					tmp = self.tmpname()
					self.func.add_variable(c.Decl(tmp, self.PyObjectP(tmp)))
					self.func.add(c.Assignment('=', c.ID(tmp), c.FuncCall(c.ID('PyObject_GetAttrString'),
															c.ExprList(c.ID(self.globals.owner.name + '_mod'), c.Constant('string', str(sym.name))))))
					self.func.add(self._error_if_null(tmp, self.func.cleanup))
					self.func.cleanup.append(tmp)
					return tmp
			except KeyError:
				pass
			# import from the builtins namespace
			if str(node) in PY_BUILTINS:
				n = self.tmpname()
				self.func.add_variable(c.Decl(n, self.PyObjectP(n)))
				self.func.add(c.Assignment('=', c.ID(n), c.FuncCall(c.ID('PyObject_GetAttrString'),
																		c.ExprList(c.ID('builtins'), c.Constant('string', str(node))))))
				self.func.add(self._error_if_null(n, self.func.cleanup))
				self.func.cleanup.append(n)
				return n
		"""

	def visit_Num(self, node):
		node.hl.create_instance(self.func.tmpname())
		node.hl.inst.declare(self.func)
		node.hl.inst.new(self.func, node.n)
		return node.hl.inst.name

		#tmp = self.tmpname()
		#self.func.add_variable(c.Decl(tmp, self.PyObjectP(tmp)))
		#if isinstance(node.n, int):
		#	if node.n < 2 ** 63 - 1:
		#		self.func.add(c.Assignment('=', c.ID(tmp), c.FuncCall(c.ID('PyLong_FromLong'), c.ExprList(c.Constant('integer', node.n)))))
		#	else:
		#		self.func.add(c.Assignment('=', c.ID(tmp), c.FuncCall(c.ID('PyLong_FromString'), c.ExprList(
		#																	c.Constant('string', str(node.n)), c.ID('NULL'), c.Constant('integer', 0)))))
		#self.func.add(self._error_if_null(tmp, self.func.cleanup))
		#self.func.cleanup.append(tmp)
		#return tmp


	def visit_Return(self, node):
		if node.value:
			# return a specific value
			name = self.visit(node.value)
			self.func.cleanup.remove(name)
			for n in self.func.cleanup:
				self.func.add(c.FuncCall(c.ID('Py_DECREF'), c.ExprList(c.ID(n))))
			self.func.add(c.Return(c.ID(name)))
		else:
			# return an implicit None
			for n in self.func.cleanup:
				self.func.add(c.FuncCall(c.ID('Py_DECREF'), c.ExprList(c.ID(n))))
			self.func.add(c.Return(c.ID('None')))


	def visit_Str(self, node):
		tmp = self.tmpname()
		self.func.add_variable(c.Decl(tmp, self.PyObjectP(tmp)))
		self.func.add(c.Assignment('=', c.ID(tmp), c.FuncCall(c.ID('PyUnicode_FromString'), c.ExprList(c.Constant('string', self.str2c(node.s))))))
		self.func.add(self._error_if_null(tmp, self.func.cleanup))
		self.func.cleanup.append(tmp)
		return tmp



	"""

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
