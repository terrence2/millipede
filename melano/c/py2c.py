'''
Copyright (c) 2011, Terrence Cole.
All rights reserved.
'''
from . import ast as c
from contextlib import contextmanager
from melano.c.pybuiltins import PY_BUILTINS
from melano.c.types.pyobject import PyObjectType
from melano.c.types.pystring import PyStringType
from melano.c.types.pytuple import PyTupleType
from melano.parser import ast as py
from melano.parser.visitor import ASTVisitor
import itertools
import pdb
import tc



class Py2C(ASTVisitor):
	'''
	Use the type information to lay out low-level code (or high-level code as needed).
	
	Options:
	(All options default to false and must be turned on by setting them to true as a kwarg.)

		elide_docstrings		If set, all __doc__ nodes will be set None, even if the docstring is present 
		static_globals			Assume that module global names are not imported or modified outside of
										the files we are processing.  If set, we can use c-level vars for globals, 
										instead of the globals dict.
	'''
	def __init__(self, **kwargs):
		super().__init__()

		# options
		self.opt_elide_docstrings = kwargs.get('elide_docstrings', False)
		self.opt_static_globals = kwargs.get('static_globals', False)

		# the python hl walker context
		self.globals = None
		self.scopes = []

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
					c.FuncCall(c.ID('assert'), c.ExprList(c.BinaryOp('==', c.FuncCall(c.ID('sizeof'), c.ExprList(c.ID('wchar_t'))), c.Constant('integer', 4)))),
					c.FuncCall(c.ID('Py_Initialize'), c.ExprList()),
					c.Assignment('=', c.ID('builtins'), c.FuncCall(c.ID('PyImport_ImportModule'), c.ExprList(c.Constant('string', 'builtins')))),
					c.Assignment('=', c.ID('None'), c.FuncCall(c.ID('PyObject_GetAttrString'), c.ExprList(c.ID('builtins'), c.Constant('string', 'None')))),
			)
		)
		self.tu.add_fwddecl(self.main.decl)
		self.tu.add(self.main)

		# the low-level statment emission context... e.g. the Compound for functions, ifs, etc.
		self.func = self.main.body


	def close(self):
		self.main.add(c.FuncCall(c.ID('Py_Finalize'), c.ExprList()))
		self.main.add(c.Return(c.Constant('integer', 0)))


	@contextmanager
	def global_scope(self, ctx):
		assert self.globals is None
		assert self.scopes == []
		self.globals = ctx
		self.scopes = [self.globals]
		yield
		self.scopes = []
		self.globals = None


	@contextmanager
	def new_scope(self, ctx):
		self.scopes.append(ctx)
		yield
		self.scopes.pop()


	@contextmanager
	def new_func(self, func):
		prior = self.func
		self.func = func
		with self.new_context(func.body):
			yield
		self.func = prior


	@contextmanager
	def new_context(self, ctx):
		#prior = self.func
		#self.func = ctx
		yield
		#self.func = prior


	@property
	def scope(self):
		return self.scopes[-1]


	def split_docstring(self, nodes:[py.AST]) -> (tc.Nonable(str), [py.AST]):
		'''Given the body, will pull off the docstring node and return it and the rest of the body.'''
		if nodes and isinstance(nodes[0], py.Expr) and isinstance(nodes[0].value, py.Str):
			if self.opt_elide_docstrings:
				return None, nodes[1:]
			return nodes[0].value.s, nodes[1:]
		return None, nodes


	def visit_Module(self, node):
		# get the MelanoModule and Name
		modscope = node.hl
		modname = modscope.owner

		# modules need 3 global names:
		#		1) the module itself (modname.global_name)
		#		2) the module's scope dict (modscope.ll_scope)
		#		3) the module builder function (modscope.ll_runner)
		modname.global_name = self.tu.reserve_name(modname.global_name, modname)
		modscope.ll_scope = self.tu.reserve_name(modname.global_name + '_dict', modscope)
		modscope.ll_runner = self.tu.reserve_name(modname.global_name + '_builder', modscope)

		# create the module creation function
		self.module_func = self.func = c.FuncDef(
			c.Decl(modscope.ll_runner,
				c.FuncDecl(
						c.ParamList(),
						c.PtrDecl(c.TypeDecl(modscope.ll_runner, c.IdentifierType('PyObject'))))),
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
				ps.assign_none(self.func)
			ps.declare(self.func) # note: this can come after we use the name, it just has to happen
			modscope.inst.set_item(self.func, name, ps.name)

		# the return value
		self.func.add_variable(c.Decl('__return_value__', c.PtrDecl(c.TypeDecl('__return_value__', c.IdentifierType('PyObject'))), init=c.ID('NULL')))

		# visit all children
		with self.global_scope(modscope):
			self.visit_nodelist(body)

		# return the module
		self.func.add(c.Assignment('=', c.ID('__return_value__'), c.ID(modname.global_name)))
		self.func.add(c.Label('end'))
		self.func.cleanup.remove(modname.global_name)
		for name in reversed(self.func.cleanup):
			self.func.add(c.FuncCall(c.ID('Py_XDECREF'), c.ExprList(c.ID(name))))
		self.func.add(c.Return(c.ID('__return_value__')))

		# add the function call to the main to set the module's global name
		tmp = self.main.reserve_name(self.main.tmpname(), modname, self.tu)
		self.main.add_variable(c.Decl(tmp, c.PtrDecl(c.TypeDecl(tmp, c.IdentifierType('PyObject')))))
		self.main.add(c.Assignment('=', c.ID(tmp), c.FuncCall(c.ID(modscope.ll_runner), c.ExprList())))
		self.main.add(c.If(c.UnaryOp('!', c.ID(tmp)), c.Compound(
								c.FuncCall(c.ID('PyErr_Print'), c.ExprList()),
								c.Return(c.Constant('integer', 1),
							)), None))


	def find_owning_parent_scope(self, node):
		name = str(node)
		pos = len(self.scopes) - 1
		current = self.scopes[pos]
		while not current.owns_name(name):
			pos -= 1
			current = self.scopes[pos]
			if pos < 0:
				break
		return pos, current


	def visit_Assign(self, node):
		val = self.visit(node.value)
		for target in node.targets:
			tgt = self.visit(target)

			if isinstance(target, py.Attribute):
				# set the value on the attribute, under the hl name of the attr
				target.value.hl.inst.set_attr(self.func, str(target.attr), val.name)

			elif isinstance(target, py.Name):
				if target.hl.is_global and self.scope != self.globals:
					self.globals.inst.set_item(self.func, str(target), node.value.hl.inst.name)

				elif target.hl.is_nonlocal:
					pos, ctx = self.find_owning_parent_scope(target)
					if pos >= 0:
						ctx.inst.set_item(self.func, str(target), node.value.hl.inst.name)
					elif pos == -1:
						raise NotImplementedError('overriding builtin with nonlocal keyword')

				else:
					#TODO: completely elide this step if we have no closure that could ref vars in this scope
					#		note: this opt needs to continue always putting things in the global scope
					self.scope.inst.set_item(self.func, str(target), node.value.hl.inst.name)

					# also create a node in the local namespace to speed up access to the node
					tgt.assign_name(self.func, val.name)

			else:
				raise NotImplementedError("Don't know how to assign to type: {}".format(type(target)))


	def visit_Attribute(self, node):
		if node.ctx == py.Store:
			# emit normal processing for name, constant, expr, etc on the left
			self.visit(node.value)

		elif node.ctx == py.Load:
			# load the attr into a local temp variable
			inst = self.visit(node.value)
			tmp = PyObjectType(self.func.tmpname())
			tmp.declare(self.func)
			inst.get_attr(self.func, str(node.attr), tmp.name)
			return tmp


	def visit_BinOp(self, node):
		l = self.visit(node.left)
		r = self.visit(node.right)

		#FIXME: the node's hl already has the coerced type; do coercion to that type before oping

		node.hl.create_instance(self.func.tmpname())
		node.hl.inst.declare(self.func)

		if node.op == py.Add:
			#NOTE: python detects str + str at runtime and skips dispatch through PyNumber_Add
			l.add(self.func, r.name, node.hl.inst.name)
		else:
			raise NotImplementedError

		return node.hl.inst


	def visit_Call(self, node):
		#TODO: direct calling, keywords calling, etc
		#TODO: track "type" so we can dispatch to PyCFunction_Call or PyFunction_Call instead of PyObject_Call 
		#TODO: track all call methods (callsite usage types) and see if we can't unpack into a direct c call

		# prepare the func name node
		funcinst = self.visit(node.func)

		# get ids of positional args
		pos_args = []
		if node.args:
			for arg in node.args:
				idinst = self.visit(arg)
				pos_args.append(idinst.name)

		# build a tuple with our positional args	
		args = PyTupleType(self.func.reserve_name(funcinst.name + '_args', None, self.tu))
		args.declare(self.func)
		args.pack(self.func, *pos_args)

		# make the call
		rv = funcinst.call(self.func, args, None)

		# cleanup the args
		args.delete(self.func)

		return rv


	def visit_FunctionDef(self, node):
		#TODO: keyword functions and other call types
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
		# get the Scope and Name
		funcscope = node.hl
		funcname = funcscope.owner

		# functions need 3 global names and 1 module-level name:
		#		1) the PyCFunction object itself (funcname.global_name)
		#		2) the function's scope dict (funcscope.ll_scope)
		#		3) the function itself (modscope.ll_runner)
		funcname.global_name = self.tu.reserve_name(funcname.global_name, funcname)
		funcscope.ll_scope = self.tu.reserve_name(funcname.global_name + '_dict', funcscope)
		funcscope.ll_runner = self.tu.reserve_name(funcname.global_name + '_runner', funcscope)
		funcdef_name = self.module_func.reserve_name(funcname.ll_name + '_def', None, self.tu)

		# create the runner function
		func = c.FuncDef(
			c.Decl(funcscope.ll_runner,
				c.FuncDecl(c.ParamList(
									c.Decl('self', c.PtrDecl(c.TypeDecl('self', c.IdentifierType('PyObject')))),
									c.Decl('args', c.PtrDecl(c.TypeDecl('args', c.IdentifierType('PyObject'))))), \
						c.PtrDecl(c.TypeDecl(funcscope.ll_runner, c.IdentifierType('PyObject'))))),
			c.Compound()
		)
		self.tu.add_fwddecl(func.decl)
		self.tu.add(func)

		# declare the PyCFunction globally
		self.tu.add_variable(c.Decl(funcname.global_name, c.PtrDecl(c.TypeDecl(funcname.global_name, c.IdentifierType('PyObject')))))

		# create the local scope dict
		funcscope.create_instance(funcscope.ll_scope)
		funcscope.inst.declare(self.tu, ['static'])
		funcscope.inst.new(self.module_func)
		self.module_func.cleanup.remove(funcscope.inst.name) # don't cleanup when module scope ends
		#TODO: do we want to do cleanup of our locals dicts in main before PyFinalize()?

		# query the docstring -- we actually want to declare it once in the module, but need to get the real bodylist here
		docstring, body = self.split_docstring(node.body)
		c_docstring = c.Constant('string', PyStringType.str2c(docstring)) if docstring else c.ID('NULL')

		# create the function instance in the module's scope (even for nested functions, so we only have to run the init once)
		# Note: this is awkward since we don't want to create type classes for low-level details.
		#FIXME: do we want to pass our own dict as self here?  What is the role for the last param?  Just the module name?
		#FIXME: find a way to clean this up -- maybe we do want ll type objects for non-exposed types
		self.module_func.add_variable(c.Decl(funcdef_name, c.TypeDecl(funcdef_name, c.Struct('PyMethodDef')),
				init=c.ExprList(c.Constant('string', str(node.name)), c.ID(funcscope.ll_runner), c.ID('METH_VARARGS'), c_docstring)))
		self.module_func.add(c.Assignment('=', c.ID(funcname.global_name), c.FuncCall(c.ID('PyCFunction_NewEx'), c.ExprList(
																c.UnaryOp('&', c.ID(funcdef_name)), c.ID(self.scope.ll_scope), c.ID('NULL')))))
		self.module_func.add(c.If(c.FuncCall(c.ID('unlikely'), c.ExprList(c.UnaryOp('!', c.ID(funcname.global_name)))), c.Compound(c.Goto('end')), None))

		# put the function into the scope where it was defined
		self.scope.inst.set_item(self.func, str(node.name), funcname.global_name)

		# set self.func for the duration of our stay in it		
		with self.new_func(func):
			# add the return variable annotation -- we need to use a goto for exit so we can do cleanup in one place (cleaner) and
			#	so that we can handle the control flow needed for exception handler much more easily.
			self.func.add_variable(c.Decl('__return_value__', c.PtrDecl(c.TypeDecl('__return_value__', c.IdentifierType('PyObject'))), init=c.ID('NULL')))

			with self.new_scope(funcscope):
				self.visit_nodelist(body)

			# exit handler
			self.func.add(c.Label('end'))
			for name in func.cleanup:
				self.func.add(c.FuncCall(c.ID('Py_XDECREF'), c.ExprList(c.ID(name))))
			self.func.add(c.Return(c.ID('__return_value__')))

		return funcname


	def visit_If(self, node):
		inst = self.visit(node.test)
		if isinstance(inst, PyObjectType):
			tmpvar = inst.is_true(self.func)
			test = c.BinaryOp('==', c.Constant('integer', 1), c.ID(tmpvar))
		else:
			raise NotImplementedError('Non-pyobject as value for If test')

		stmt = c.If(test, c.Compound(), None)
		with self.new_context(stmt.iftrue):
			self.visit_nodelist(node.body)

		self.func.add(stmt)


	def visit_Name(self, node):
		# if we are storing to the name, we just need to return the instance, so we can assign to it
		if node.ctx == py.Store:
			#NOTE: names will not get out of sync here because they share the same underlying Name, so the rename
			#		happens for all shared names in a Scope.
			if not self.func.has_symbol(node.hl) and not node.hl.is_global and not node.hl.is_nonlocal:
				node.hl.ll_name = self.func.reserve_name(node.hl.ll_name, node.hl, self.tu)
				node.hl.create_instance(node.hl.ll_name)
				node.hl.inst.declare(self.func)

			return node.hl.inst

		# if we are loading a name, we have to search for the name's location 
		elif node.ctx == py.Load:
			# Since we already indexed, we know what can be found in our local scopes.  Look up the scope
			# chain until we find a local with the given name.  If we hit scope[0] (globals), then emit code to 
			# try globals, then fall back to builtins, unless static_globals is set, in which case, we can continue
			# all the way to the top and only fallback to builtins.  Of course, if the name is present in the top
			# scope, then we can just access the name locally.
			name = str(node)

			#FIXME: this needs to abort properly on use before set errors, rather than looking up-scope

			# if the node is declared and stored into from this scope; and there is no closure which could modify us;
			#	and the scope is not globals; then we can use it directly
			if node.hl.inst and not self.scope.has_closure() and self.scope != self.globals and self.scope.owns_name(name) and self.func.has_name(node.hl.inst.name):
				return node.hl.inst

			# find the proper scope for access
			lvl, scope = self.find_owning_parent_scope(node)

			# TODO: if not in globals, check against builtins and just go there if we are opt_static_globals

			if lvl <= 0:
				#NOTE: we have to create fully generic code to access globals and builtins, since they can change under us
				tmp = self.func.tmpname()
				node.hl.inst = PyObjectType(tmp)
				node.hl.inst.declare(self.func)

				# access globals first, fall back to builtins -- remember to ref the global if we get it, sine dict get item borrows
				self.func.add(c.Assignment('=', c.ID(tmp), c.FuncCall(c.ID('PyDict_GetItemString'), c.ExprList(c.ID(self.globals.ll_scope), c.Constant('string', name)))))
				self.func.add(c.If(c.UnaryOp('!', c.ID(tmp)),
						c.Compound(
							c.Assignment('=', c.ID(tmp), c.FuncCall(c.ID('PyObject_GetAttrString'),
																c.ExprList(c.ID('builtins'), c.Constant('string', name)))),
							c.If(c.UnaryOp('!', c.ID(tmp)), c.Compound(c.Goto('end')), None)
						),
						c.Compound(
							c.FuncCall(c.ID('Py_INCREF'), c.ExprList(c.ID(tmp)))
						)))
				node.hl.inst.fail_if_null(tmp, self.func)
				self.func.cleanup.append(tmp)
			else:
				#For higher non-local scopes, we can access directly
				assert scope.has_name(name)
				tmp = self.func.tmpname()
				node.hl.create_instance(tmp)
				node.hl.inst.declare(self.func)
				scope.inst.get_item(self.func, name, node.hl.inst.name)

			return node.hl.inst


	def visit_Num(self, node):
		node.hl.create_instance(self.func.tmpname())
		node.hl.inst.declare(self.func)
		node.hl.inst.new(self.func, node.n)
		return node.hl.inst


	def visit_Return(self, node):
		if node.value:
			# return a specific value
			inst = self.visit(node.value)
			self.func.add(c.Assignment('=', c.ID('__return_value__'), c.ID(inst.name)))
			self.func.add(c.Goto('end'))
		else:
			self.func.add(c.Assignment('=', c.ID('__return_value__'), c.ID('None')))
			self.func.add(c.Goto('end'))


	def visit_Str(self, node):
		node.hl.create_instance(self.func.tmpname())
		node.hl.inst.declare(self.func)
		node.hl.inst.new(self.func, node.s)
		return node.hl.inst



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
				#self.func.import_python(str(alias.name))
				print('IMP:', alias.name.hl.name)

	#def visit_ImportFrom(self, node):
	#	#import pdb;pdb.set_trace()
	#	self.func.import_from(node.level, str(node.module), [str(n) for n in node.names])


	def visit_If(self, node):
		self.visit(node.test)
		print(node.test.hl.name)
		#ctx = self.func.create_if():
		#with self.scope(ctx):
		#	self.visit_nodelist(nodes)

	def visit_Compare(self, node):
		self.visit(node.left)

	def visit_If(self, node):
		with self.scope(self.func.if_stmt()):
			self.visit(node.test)
		with self.scope(self.func.block()):
			self.visit_nodelist(node.body)
		if node.orelse:
			self.func.else_stmt()
			with self.scope(self.func.block()):
				self.visit_nodelist(node.orelse)
	"""
