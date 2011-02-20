'''
Copyright (c) 2011, Terrence Cole.
All rights reserved.
'''
from . import ast as c
from contextlib import contextmanager
from melano.c.pybuiltins import PY_BUILTINS
from melano.c.types.integer import CIntegerType
from melano.c.types.pycfunction import PyCFunctionType
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
	# map from ast comparison types to rich comparator values
	COMPARATORS_RICH = {
		py.Lt: 'Py_LT',
		py.LtE: 'Py_LE',
		py.Eq: 'Py_EQ',
		py.NotEq: 'Py_NE',
		py.Gt: 'Py_GT',
		py.GtE: 'Py_GE',
	}
	COMPARATORS_PRETTY = {
		py.Lt: '<',
		py.LtE: '<=',
		py.Eq: '==',
		py.NotEq: '!=',
		py.Gt: '>',
		py.GtE: '>=',
		py.Is: 'is',
		py.IsNot: 'is not',
		py.In: 'in',
		py.NotIn: 'not in',
	}


	def __init__(self, **kwargs):
		super().__init__()

		# Emit helpful source-level comments
		self.debug = True

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
					c.FuncCall(c.ID('assert'), c.ExprList(c.BinaryOp(' == ', c.FuncCall(c.ID('sizeof'), c.ExprList(c.ID('Py_UNICODE'))), c.Constant('integer', 4)))),
					c.FuncCall(c.ID('assert'), c.ExprList(c.BinaryOp(' == ', c.FuncCall(c.ID('sizeof'), c.ExprList(c.ID('wchar_t'))), c.Constant('integer', 4)))),
					c.FuncCall(c.ID('Py_Initialize'), c.ExprList()),
					c.Assignment(' = ', c.ID('builtins'), c.FuncCall(c.ID('PyImport_ImportModule'), c.ExprList(c.Constant('string', 'builtins')))),
					c.Assignment(' = ', c.ID('None'), c.FuncCall(c.ID('PyObject_GetAttrString'), c.ExprList(c.ID('builtins'), c.Constant('string', 'None')))),
			)
		)
		self.tu.add_fwddecl(self.main.decl)
		self.tu.add(self.main)

		# the low-level statment emission context... e.g. the Compound for functions, ifs, etc.
		self.context = self.main.body


	def close(self):
		self.main.body.add(c.FuncCall(c.ID('Py_Finalize'), c.ExprList()))
		self.main.body.add(c.Return(c.Constant('integer', 0)))


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
	def new_scope(self, scope, ctx):
		# add the new scope and set the scope's context
		self.scopes.append(scope)
		scope.context = ctx
		# set the new global output context
		prior_ctx = self.context
		self.context = ctx
		yield
		# drop the scope
		self.scopes.pop()
		# reset context
		self.context = prior_ctx


	@contextmanager
	def new_context(self, ctx):
		'''Sets a new context (e.g. C-level {}), without adjusting the python scope or the c scope-context'''
		prior = self.context
		self.context = ctx
		yield
		self.context = prior


	@property
	def scope(self):
		return self.scopes[-1]


	def comment(self, cmt):
		'''Optionally add a comment node to the source at the current location.'''
		if self.debug:
			self.context.add(c.Comment(cmt))


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
		self.module_func = c.FuncDef(
			c.Decl(modscope.ll_runner,
				c.FuncDecl(
						c.ParamList(),
						c.PtrDecl(c.TypeDecl(modscope.ll_runner, c.IdentifierType('PyObject'))))),
			c.Compound()
		)
		self.tu.add_fwddecl(self.module_func.decl)
		self.tu.add(self.module_func)

		# set the initial context
		self.context = self.module_func.body
		self.comment('Create module "{}" as "{}"'.format(modscope.name, modname.name))

		# create the module
		modname.create_instance(modname.global_name)
		modname.inst.declare(self.tu, ['static'])
		modname.inst.new(self.context, modname.name)

		# load the module dict from the module to the scope
		modscope.create_instance(modscope.ll_scope)
		modscope.inst.declare(self.tu, ['static'])
		modname.inst.get_dict(self.context, modscope.inst)

		# load and attach special attributes to the module dict
		docstring, body = self.split_docstring(node.body)
		for name, s in [('__name__', modname.name), ('__file__', modscope.filename), ('__doc__', docstring)]:
			if s is not None:
				ps = PyStringType(self.context.reserve_name(name, None, self.tu))
				ps.new(self.context, s)
			else:
				ps = PyObjectType(self.context.reserve_name(name, None, self.tu))
				ps.assign_none(self.context)
			ps.declare(self.context) # note: this can come after we use the name, it just has to happen
			modscope.inst.set_item(self.context, name, ps.name)

		# the return value
		self.context.add_variable(c.Decl('__return_value__', c.PtrDecl(c.TypeDecl('__return_value__', c.IdentifierType('PyObject'))), init=c.ID('NULL')), False)

		# visit all children
		with self.global_scope(modscope):
			# record the top-level context in the scope, so we can declare toplevel variables when in a sub-contexts
			self.scope.context = self.context

			# visit all children
			self.visit_nodelist(body)

		# return the module
		self.context.add(c.Assignment('=', c.ID('__return_value__'), c.ID(modname.global_name)))
		self.context.add(c.Label('end'))
		for name in reversed(self.context.cleanup):
			self.context.add(c.FuncCall(c.ID('Py_XDECREF'), c.ExprList(c.ID(name))))
		self.context.add(c.Return(c.ID('__return_value__')))

		# add the function call to the main to set the module's global name
		tmp = self.main.body.reserve_name(self.main.body.tmpname(), modname, self.tu)
		self.main.body.add_variable(c.Decl(tmp, c.PtrDecl(c.TypeDecl(tmp, c.IdentifierType('PyObject')))))
		self.main.body.add(c.Assignment('=', c.ID(tmp), c.FuncCall(c.ID(modscope.ll_runner), c.ExprList())))
		self.main.body.add(c.If(c.UnaryOp('!', c.ID(tmp)), c.Compound(
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
				target.value.hl.inst.set_attr(self.context, str(target.attr), val)

			elif isinstance(target, py.Name):
				if target.hl.is_global and self.scope != self.globals:
					self.globals.inst.set_item(self.context, str(target), node.value.hl.inst.name)

				elif target.hl.is_nonlocal:
					pos, ctx = self.find_owning_parent_scope(target)
					if pos >= 0:
						ctx.inst.set_item(self.context, str(target), node.value.hl.inst.name)
					elif pos == -1:
						raise NotImplementedError('overriding builtin with nonlocal keyword')

				else:
					#TODO: completely elide this step if we have no closure that could ref vars in this scope
					#		note: this opt needs to continue always putting things in the global scope
					self.scope.inst.set_item(self.context, str(target), val.name)

					# also create a node in the local namespace to speed up access to the node
					tgt.assign_name(self.context, val)

			else:
				raise NotImplementedError("Don't know how to assign to type: {}".format(type(target)))


	def visit_Attribute(self, node):
		if node.ctx == py.Store:
			# emit normal processing for name, constant, expr, etc on the left
			self.visit(node.value)

		elif node.ctx == py.Load:
			# load the attr into a local temp variable
			inst = self.visit(node.value)
			self.comment('Load Attribute "{}.{}"'.format(str(node.value), str(node.attr)))
			tmp = PyObjectType(self.context.tmpname())
			tmp.declare(self.context)
			inst.get_attr(self.context, str(node.attr), tmp.name)
			return tmp


	def visit_BinOp(self, node):
		l = self.visit(node.left)
		r = self.visit(node.right)

		#FIXME: the node's hl already has the coerced type; do coercion to that type before oping

		node.hl.create_instance(self.context.tmpname())
		node.hl.inst.declare(self.context)

		if node.op == py.Add:
			#NOTE: python detects str + str at runtime and skips dispatch through PyNumber_Add
			l.add(self.context, r, node.hl.inst)
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
				idinst = idinst.as_pyobject(self.context)
				idinst.incref(self.context) # pytuple pack will steal the ref, but we want to be able to cleanup the node later
				pos_args.append(idinst.name)

		# begin call output
		self.comment('Call function "{}"'.format(str(node.func)))

		# build the output variable
		rv = PyObjectType(self.context.reserve_name(funcinst.name + '_rv', None, self.tu))
		rv.declare(self.context)

		# build a tuple with our positional args	
		args = PyTupleType(self.context.reserve_name(funcinst.name + '_args', None, self.tu))
		args.declare(self.context)
		args.pack(self.context, *pos_args)

		# make the call
		funcinst.call(self.context, args, None, rv)

		# cleanup the args
		args.delete(self.context)

		return rv


	def visit_Compare(self, node):
		# format and print the op we are doing for sanity sake
		s = 'Compare ' + str(node.left)
		for o, b in zip(node.ops, node.comparators):
			s += ' {} {}'.format(self.COMPARATORS_PRETTY[o], str(b))
		self.comment(s)

		# initialize new tmp variable with default value of false
		out = CIntegerType(self.context.tmpname(), is_a_bool=True)
		out.declare(self.context, init=0)

		# store this because when we bail we will come all the way back to our starting context at once
		base_context = self.context

		# make each comparison in order
		a = self.visit(node.left)
		a = a.as_pyobject(self.context)
		for op, b in zip(node.ops, node.comparators):
			b = self.visit(b)
			b = b.as_pyobject(self.context)

			# do one compare; only continue to next scope if we succeed
			if op in self.COMPARATORS_RICH:
				rv = a.rich_compare_bool(self.context, b, self.COMPARATORS_RICH[op])
			elif op == py.In:
				rv = b.sequence_contains(self.context, a)
			elif op == py.NotIn:
				rv = b.sequence_contains(self.context, a)
				rv = rv.not_(self.context)
			elif op == py.Is:
				rv = a.is_(self.context, b)
			elif op == py.IsNot:
				rv = a.is_(self.context, b)
				rv = rv.not_(self.context)
			else:
				raise NotImplementedError("unimplemented comparator in visit_compare: {}".format(op))
			stmt = c.If(c.ID(rv.name), c.Compound(), None)
			self.context.add(stmt)
			self.context = stmt.iftrue

			# next lhs is current rhs
			a = b

		# we are in our deepest nested context now, where all prior statements have been true
		self.context.add(c.Assignment('=', c.ID(out.name), c.Constant('integer', 1)))

		# reset the context
		self.context = base_context

		return out


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
		funcdef_name = self.module_func.body.reserve_name(funcname.ll_name + '_def', None, self.tu)

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
		self.module_func.body.add(c.Comment('Declare Function "{}"'.format(funcname.name)))

		# create the local scope dict
		funcscope.create_instance(funcscope.ll_scope)
		funcscope.inst.declare(self.tu, ['static'])
		funcscope.inst.new(self.module_func.body)
		#TODO: do we want to do cleanup of our locals dicts in main before PyFinalize()?

		# query the docstring -- we actually want to declare it once in the module, but need to get the real bodylist here
		docstring, body = self.split_docstring(node.body)
		c_docstring = c.Constant('string', PyStringType.str2c(docstring)) if docstring else c.ID('NULL')

		# create the function instance in the module's scope (even for nested functions, so we only have to run the init once)
		# Note: this is awkward since we don't want to create type classes for low-level details.
		#FIXME: do we want to pass our own dict as self here?  What is the role for the last param?  Just the module name?
		#FIXME: find a way to clean this up -- maybe we do want ll type objects for non-exposed types
		self.module_func.body.add_variable(c.Decl(funcdef_name, c.TypeDecl(funcdef_name, c.Struct('PyMethodDef')),
				init=c.ExprList(c.Constant('string', str(node.name)), c.ID(funcscope.ll_runner), c.ID('METH_VARARGS'), c_docstring)), False)
		cfunc_inst = PyCFunctionType(funcname.global_name)
		cfunc_inst.declare(self.tu, ['static'])
		cfunc_inst.new(self.module_func.body, funcdef_name, funcscope.inst, 'NULL')

		# put the function into the scope where it was defined
		self.scope.inst.set_item(self.context, str(node.name), funcname.global_name)

		# set self.context for the duration of our stay in it		
		with self.new_scope(funcscope, func.body):
			# add the return variable annotation -- we need to use a goto for exit so we can do cleanup in one place (cleaner) and
			#	so that we can handle the control flow needed for exception handler much more easily.
			self.context.add_variable(c.Decl('__return_value__', c.PtrDecl(c.TypeDecl('__return_value__', c.IdentifierType('PyObject'))), init=c.ID('NULL')), False)

			self.visit_nodelist(body)

			# exit handler
			self.context.add(c.Label('end'))
			for name in func.body.cleanup:
				self.context.add(c.FuncCall(c.ID('Py_XDECREF'), c.ExprList(c.ID(name))))
			self.context.add(c.Return(c.ID('__return_value__')))

		return funcname


	def visit_If(self, node):
		inst = self.visit(node.test)
		if isinstance(inst, PyObjectType):
			tmpvar = inst.is_true(self.context)
			test = c.BinaryOp('==', c.Constant('integer', 1), c.ID(tmpvar))
		elif isinstance(inst, CIntegerType):
			test = c.ID(inst.name)
		else:
			raise NotImplementedError('Non-pyobject as value for If test')

		stmt = c.If(test, c.Compound(), c.Compound() if node.orelse else None)
		with self.new_context(stmt.iftrue):
			self.visit_nodelist(node.body)
		if node.orelse:
			with self.new_context(stmt.iffalse):
				self.visit_nodelist(node.orelse)

		self.context.add(stmt)


	def visit_Name(self, node):
		# if we are storing to the name, we just need to return the instance, so we can assign to it
		if node.ctx == py.Store:
			#NOTE: names will not get out of sync here because they share the same underlying Name, so the rename
			#		happens for all shared names in a Scope.
			if not node.hl.inst:
				node.hl.ll_name = self.scope.context.reserve_name(node.hl.ll_name, node.hl, self.tu)
				node.hl.create_instance(node.hl.ll_name)
				node.hl.inst.declare(self.scope.context)
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
			if node.hl.inst and not self.scope.has_closure() and self.scope != self.globals and self.scope.owns_name(name) and self.scope.context.has_name(node.hl.inst.name):
				return node.hl.inst

			# find the proper scope for access
			lvl, scope = self.find_owning_parent_scope(node)

			# TODO: if not in globals, check against builtins and just go there if we are opt_static_globals

			if lvl <= 0:
				#NOTE: we have to create fully generic code to access globals and builtins, since they can change under us
				tmp = self.scope.context.tmpname()
				node.hl.inst = PyObjectType(tmp)
				node.hl.inst.declare(self.scope.context)

				# note; unless we declare that module globals are static (and thus fully discovered and unoverridable, we need
				#		to check them first... the best op in this case is checking if the override is likely or not.
				if name in PY_BUILTINS:
					self.comment('Load (probable) builtin "{}"'.format(name))
					mode = 'likely'
				else:
					self.comment('Load (probable) global "{}"'.format(name))
					mode = 'unlikely'

				# access globals first, fall back to builtins -- remember to ref the global if we get it, since dict get item borrows
				self.context.add(c.Assignment('=', c.ID(tmp), c.FuncCall(c.ID('PyDict_GetItemString'), c.ExprList(c.ID(self.globals.ll_scope), c.Constant('string', name)))))
				self.context.add(c.If(c.FuncCall(c.ID(mode), c.ExprList(c.UnaryOp('!', c.ID(tmp)))),
						c.Compound(
							c.Assignment('=', c.ID(tmp), c.FuncCall(c.ID('PyObject_GetAttrString'),
																c.ExprList(c.ID('builtins'), c.Constant('string', name)))),
							c.If(c.FuncCall(c.ID('unlikely'), c.ExprList(c.UnaryOp('!', c.ID(tmp)))), c.Compound(c.Goto('end')), None)
						),
						c.Compound(
							c.FuncCall(c.ID('Py_INCREF'), c.ExprList(c.ID(tmp)))
						)))
				node.hl.inst.fail_if_null(self.context, tmp)
			else:
				#For higher non-local scopes, we can access directly
				assert scope.has_name(name)
				tmp = self.context.tmpname()
				node.hl.create_instance(tmp)
				node.hl.inst.declare(self.context)
				scope.inst.get_item(self.context, name, node.hl.inst)

			return node.hl.inst


	def visit_Num(self, node):
		node.hl.create_instance(self.context.tmpname())
		node.hl.inst.declare(self.context)
		node.hl.inst.new(self.context, node.n)
		return node.hl.inst


	def visit_Return(self, node):
		if node.value:
			# return a specific value
			inst = self.visit(node.value)
			self.context.add(c.Assignment('=', c.ID('__return_value__'), c.ID(inst.name)))
			self.context.add(c.Goto('end'))
		else:
			self.context.add(c.Assignment('=', c.ID('__return_value__'), c.ID('None')))
			self.context.add(c.Goto('end'))


	def visit_Str(self, node):
		node.hl.create_instance(self.context.tmpname())
		node.hl.inst.declare(self.context)
		node.hl.inst.new(self.context, node.s)
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
