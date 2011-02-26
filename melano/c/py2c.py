'''
Copyright (c) 2011, Terrence Cole.
All rights reserved.
'''
from . import ast as c
from contextlib import contextmanager
from melano.c.pybuiltins import PY_BUILTINS
from melano.c.types.integer import CIntegerType
from melano.c.types.lltype import LLType
from melano.c.types.pycfunction import PyCFunctionType
from melano.c.types.pydict import PyDictType
from melano.c.types.pyobject import PyObjectType
from melano.c.types.pystring import PyStringType
from melano.c.types.pytuple import PyTupleType
from melano.c.types.pytype import PyTypeType
from melano.parser import ast as py
from melano.lang.visitor import ASTVisitor
from melano.project.module import MelanoModule
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
			c.Decl('__melano_main__',
				c.FuncDecl(c.ParamList(
						c.Decl('argc', c.TypeDecl('argc', c.IdentifierType('int'))),
						c.Decl('argv', c.PtrDecl(c.PtrDecl(c.TypeDecl('argv', c.IdentifierType('wchar_t')))))),
					c.TypeDecl('__melano_main__', c.IdentifierType('int')))
			),
			c.Compound(
					c.FuncCall(c.ID('assert'), c.ExprList(c.BinaryOp(' == ', c.FuncCall(c.ID('sizeof'), c.ExprList(c.ID('Py_UNICODE'))), c.Constant('integer', 4)))),
					c.FuncCall(c.ID('assert'), c.ExprList(c.BinaryOp(' == ', c.FuncCall(c.ID('sizeof'), c.ExprList(c.ID('wchar_t'))), c.Constant('integer', 4)))),
					c.FuncCall(c.ID('Py_Initialize'), c.ExprList()),
					c.FuncCall(c.ID('PySys_SetArgv'), c.ExprList(c.ID('argc'), c.ID('argv'))),
					c.Assignment(' = ', c.ID('builtins'), c.FuncCall(c.ID('PyImport_ImportModule'), c.ExprList(c.Constant('string', 'builtins')))),
					c.Assignment(' = ', c.ID('None'), c.FuncCall(c.ID('PyObject_GetAttrString'), c.ExprList(c.ID('builtins'), c.Constant('string', 'None')))),
			)
		)
		self.tu.add_fwddecl(self.main.decl)
		self.tu.add(self.main)

		# the low-level statment emission context... e.g. the Compound for functions, ifs, etc.
		self.context = self.main.body

		# the module we are currently processing
		self.module = None


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
		self.scopes.append(scope)
		scope.context = ctx # set the scope's low-level context
		with self.new_context(ctx):
			yield
		self.scopes.pop()


	@contextmanager
	def new_context(self, ctx):
		'''Sets a new context (e.g. C-level {}), without adjusting the python scope or the c scope-context'''
		ctx._visitor = self # give low-level access to high-level data for printing error messages

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
		self.module = node.hl

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

		# create the module's global name
		modname.create_instance(modname.global_name)
		modname.inst.declare(self.tu, ['static'])

		# set the initial context
		with self.new_context(self.module_func.body):
			# if the module is already built, return our reference
			self.context.add(c.If(c.ID(modname.inst.name), c.Compound(c.Return(c.ID(modname.inst.name))), None))

			# build the module
			self.comment('Create module "{}" as "{}"'.format(modscope.name, modname.name))
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
					ps.new(self.context, PyStringType.str2c(s))
				else:
					ps = PyObjectType(self.context.reserve_name(name, None, self.tu))
					ps.assign_none(self.context)
				ps.declare(self.context) # note: this can come after we use the name, it just has to happen
				modscope.inst.set_item_string(self.context, name, ps)

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
									c.FuncCall(c.ID('__err_show_traceback__'), c.ExprList()),
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
		self.comment("Assign: {} = {}".format([str(t) for t in node.targets], str(node.value)))
		val = self.visit(node.value)
		for target in node.targets:
			tgt = self.visit(target)
			self._store(target, tgt, val)


	def _store(self, target, tgt, val):
		'''
		Common "normal" assignment handler.  Things like for-loop targets and with-stmt vars 
			need the same full suite of potential assignment targets as normal assignments.  With
			the caveat that only assignment will have non-Name children.
		
		target -- the node that is the lhs of the storage.
		tgt -- the inst 
		'''
		#TODO: destructuring assignment

		if isinstance(target, py.Attribute):
			# set the value on the attribute, under the hl name of the attr
			target.value.hl.inst.set_attr_string(self.context, str(target.attr), val)

		elif isinstance(target, py.Subscript):
			# set the value on the attribute under the given target key
			target.value.hl.inst.set_item(self.context, tgt, val)

		elif isinstance(target, py.Name):
			# note, the hl Name or Ref will always be parented under  the right scope
			target.hl.parent.inst.set_item_string(self.context, str(target), val)

			#TODO: this is an optimization; we only want to do it when we can get away with it, and when we can
			#		get away with it, we don't want to assign to the namespace.
			#if tgt:
			#	tgt.assign_name(self.context, val)

			"""
			if target.hl.is_global and self.scope != self.globals:
				self.globals.inst.set_item_string(self.context, str(target), val)

			elif target.hl.is_nonlocal:
				pos, ctx = self.find_owning_parent_scope(target)
				if pos >= 0:
					ctx.inst.set_item_string(self.context, str(target), val)
				elif pos == -1:
					raise NotImplementedError('overriding builtin with nonlocal keyword')

			else:
				#TODO: completely elide this step if we have no closure that could ref vars in this scope
				#		note: this opt needs to continue always putting things in the global scope
				self.scope.inst.set_item_string(self.context, str(target), val)

				# also create a node in the local namespace to speed up access to the node
				if tgt:
					tgt.assign_name(self.context, val)
			"""
		else:
			raise NotImplementedError("Don't know how to assign to type: {}".format(type(target)))


	def _load(self, source):
		'''
		source - the underlying name reference that we to provide access to
		'''
		#pdb.set_trace()
		tmp = PyObjectType(self.scope.context.tmpname())
		tmp.declare(self.scope.context)

		if source.hl.parent.inst:
			source.hl.parent.inst.get_item_string(self.context, str(source), tmp)
		else:
			if str(source) in PY_BUILTINS:
				self.comment('Load (probable) builtin "{}"'.format(str(source)))
				mode = 'likely'
			else:
				self.comment('Load (probable) global "{}"'.format(str(source)))
				mode = 'unlikely'

			# access globals first, fall back to builtins -- remember to ref the global if we get it, since dict get item borrows
			self.context.add(c.Assignment('=', c.ID(tmp.name), c.FuncCall(c.ID('PyDict_GetItemString'), c.ExprList(c.ID(self.globals.ll_scope), c.Constant('string', str(source))))))
			self.context.add(c.If(c.FuncCall(c.ID(mode), c.ExprList(c.UnaryOp('!', c.ID(tmp.name)))),
					c.Compound(
						c.Assignment('=', c.ID(tmp.name), c.FuncCall(c.ID('PyObject_GetAttrString'),
															c.ExprList(c.ID('builtins'), c.Constant('string', str(source))))),
						c.If(c.FuncCall(c.ID('unlikely'), c.ExprList(c.UnaryOp('!', c.ID(tmp.name)))), c.Compound(c.Goto('end')), None)
					),
					c.Compound(
						c.FuncCall(c.ID('Py_INCREF'), c.ExprList(c.ID(tmp.name)))
					)))
			tmp.fail_if_null(self.context, tmp.name)
		return tmp


	def visit_Attribute(self, node):
		if node.ctx == py.Store:
			# emit normal processing for name, constant, expr, etc on the left
			if not node.hl.inst:
				node.hl.ll_name = self.scope.context.reserve_name(node.hl.ll_name, node.hl, self.tu)
				node.hl.create_instance(node.hl.ll_name)
				node.hl.inst.declare(self.scope.context)
			return self.visit(node.value)

		elif node.ctx == py.Load:
			# load the attr into a local temp variable
			inst = self.visit(node.value)
			self.comment('Load Attribute "{}.{}"'.format(str(node.value), str(node.attr)))
			tmp = PyObjectType(self.scope.context.tmpname())
			tmp.declare(self.scope.context)
			inst.get_attr_string(self.context, str(node.attr), tmp)
			return tmp

		else:
			raise NotImplementedError("Unknown Attribute access context: {}".format(node.ctx))


	def visit_Subscript(self, node):
		if node.ctx == py.Store:
			# Return the tgt that we will use in the assignment: the slice inst
			return self.visit(node.slice)
		elif node.ctx == py.Load:
			kinst = self.visit(node.slice)
			tgtinst = self.visit(node.value)
			tmp = PyObjectType(self.scope.context.tmpname())
			tmp.declare(self.scope.context)
			tgtinst.get_item(self.context, kinst, tmp)
			return tmp
		else:
			raise NotImplementedError("Unknown Attribute access context: {}".format(node.ctx))


	def visit_BinOp(self, node):
		l = self.visit(node.left)
		r = self.visit(node.right)

		#FIXME: the node's hl already has the coerced type; do coercion to that type before oping

		node.hl.create_instance(self.context.tmpname())
		node.hl.inst.declare(self.context)

		#TODO: python detects str + str at runtime and skips dispatch through PyNumber_Add, so we can 
		#		assume that would be faster
		if node.op == py.BitOr:
			l.bitor(self.context, r, node.hl.inst)
		elif node.op == py.BitXor:
			l.bitxor(self.context, r, node.hl.inst)
		elif node.op == py.BitAnd:
			l.bitand(self.context, r, node.hl.inst)
		elif node.op == py.LShift:
			l.lshift(self.context, r, node.hl.inst)
		elif node.op == py.RShift:
			l.rshift(self.context, r, node.hl.inst)
		elif node.op == py.Add:
			l.add(self.context, r, node.hl.inst)
		elif node.op == py.Sub:
			l.subtract(self.context, r, node.hl.inst)
		elif node.op == py.Mult:
			l.multiply(self.context, r, node.hl.inst)
		elif node.op == py.Div:
			l.divide(self.context, r, node.hl.inst)
		elif node.op == py.FloorDiv:
			l.floor_divide(self.context, r, node.hl.inst)
		elif node.op == py.Mod:
			l.modulus(self.context, r, node.hl.inst)
		elif node.op == py.Pow:
			l.power(self.context, r, node.hl.inst)
		else:
			raise NotImplementedError("BinOp({})".format(node.op))

		return node.hl.inst


	def visit_Call(self, node):
		#TODO: direct calling, keywords calling, etc
		#TODO: track "type" so we can dispatch to PyCFunction_Call or PyFunction_Call instead of PyObject_Call 
		#TODO: track all call methods (callsite usage types) and see if we can't unpack into a direct c call

		# prepare the func name node
		funcinst = self.visit(node.func)

		# just ensure we always have these nodes for simplicity
		if not node.args: node.args = []
		if not node.keywords: node.keywords = []

		# if we are defined locally, we can know the expected calling proc and reorganize our args to it
		if node.func.hl.scope:
			expect_args = node.func.hl.scope.expect_args[:]
			expect_kwargs = node.func.hl.scope.expect_kwargs[:]

		# otherwise, we have to trust that the caller is doing it right
		else:
			expect_args = [str(arg) for arg in node.args]
			expect_kwargs = [str(kw.keyword) for kw in node.keywords]

		# reorganize the passed args into the required format
		pos_args = []
		kw_args = []
		for arg in node.args:
			# fill into positional if we expect them there
			if len(expect_args):
				pos_args.append(arg)
				expect_args = expect_args[1:]
			# otherwise, fill left to right into keyworked args 
			else:
				assert len(expect_kwargs), "Not enough args passed to function: {}".format(str(node.func))
				kw_args.append(arg)
				expect_kwargs = expect_kwargs[1:]
		pos_args = pos_args + [None] * (len(expect_args) - len(pos_args)) #extend with None's so we can have random insertion
		for kw in node.keywords:
			# we need to match any passed keyword args up to remaining positional args, in the correct position
			if expect_args and str(kw.keyword) in expect_args:
				offset = expect_args.index(str(kw.keyword))
				pos_args[offset] = kw.value
				del expect_args[offset]
			elif str(kw.keyword) in expect_kwargs:
				kw_args.append(kw)
				expect_kwargs.remove(str(kw.keyword))
			else:
				raise NotImplementedError("this arg needs to go in **kwargs")
			#pdb.set_trace()

		# build the actual arg tuple/dicts
		args_insts = []
		for arg in pos_args:
			idinst = self.visit(arg)
			idinst = idinst.as_pyobject(self.context)
			args_insts.append(idinst)
		for idinst in args_insts:
			# pytuple pack will steal the ref, but we want to be able to cleanup the node later
			# note: do this after visiting all other nodes to minimize our probability of leaking the extra ref
			#FIXME: make it possible for a failure in the tuple packing to free these refs?  Or is this a bad idea
			#		because a failure halfway through would end up with us double-freeing half of our refs?
			idinst.incref(self.context)
		args1 = PyTupleType(self.scope.context.reserve_name(funcinst.name + '_args', None, self.tu))
		args1.declare(self.scope.context)
		args1.pack(self.context, *args_insts)

		'''
		if kw_args:
			args2 = PyDictType(self.scope.context.tmpname())
			args2.declare(self.scope.context)
			args2.new(self.context)
			for kw in kw_args:
				print("AT KW: {}:{}".format(str(kw.keyword), str(kw.value)))
				val_inst = self.visit(kw.value)
				args2.set_item_string(self.context, str(kw.keyword), val_inst)
		'''

		# begin call output
		self.comment('Call function "{}"'.format(str(node.func)))

		# build the output variable
		rv = PyObjectType(self.scope.context.reserve_name(funcinst.name + '_rv', None, self.tu))
		rv.declare(self.scope.context)

		# make the call
		funcinst.call(self.context, args1, None, rv)

		# cleanup the args
		args1.delete(self.context)
		#if kw_args: kw_args.delete(self.context)

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


	def visit_Dict(self, node):
		node.hl.create_instance(self.scope.context.tmpname())
		node.hl.inst.declare(self.scope.context)
		node.hl.inst.new(self.context)
		if node.keys and node.values:
			for k, v in zip(node.keys, node.values):
				kinst = self.visit(k)
				vinst = self.visit(v)
				node.hl.inst.set_item(self.context, kinst, vinst)
		return node.hl.inst


	def visit_For(self, node):
		#for <target> in <iter>: <body>
		#else: <orelse>

		#TODO: for:else/break

		tgt = self.visit(node.target)
		iter_obj = self.visit(node.iter)

		# get the PyIter for the iteration object
		iter = PyObjectType(self.scope.context.tmpname())
		iter.declare(self.scope.context)
		iter_obj.get_iter(self.context, iter)

		# the gets the object locally inside of the while expr; we do the full assignment inside the body
		stmt = c.While(c.Assignment('=', c.ID(tgt.name), c.FuncCall(c.ID('PyIter_Next'), c.ExprList(c.ID(iter.name)))), c.Compound())
		self.context.add(stmt)
		with self.new_context(stmt.stmt):
			self._store(node.target, tgt, tgt)
			self.visit_nodelist(node.body)


	def visit_FunctionDef(self, node):
		#TODO: keyword functions and other call types

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
		self.scope.inst.set_item_string(self.context, str(node.name), cfunc_inst)

		# set self.context for the duration of our stay in it		
		with self.new_scope(funcscope, func.body):
			# add the return variable annotation -- we need to use a goto for exit so we can do cleanup in one place (cleaner) and
			#	so that we can handle the control flow needed for exception handler much more easily.
			self.context.add_variable(c.Decl('__return_value__', c.PtrDecl(c.TypeDecl('__return_value__', c.IdentifierType('PyObject'))), init=c.ID('NULL')), False)

			# attach all parameters into the local namespace
			if node.args and node.args.args:
				arginst = PyTupleType('args')
				self.visit_nodelist_field(node.args.args, 'arg')
				for i, arg in enumerate(node.args.args):
					arginst.get_unchecked(self.context, i, arg.arg.hl.inst)
			#TODO:
			#self.visit(node.args.vararg)
			#self.visit_nodelist_field(node.args.kwonlyargs, 'arg')
			#self.visit(node.args.kwarg)

			# write the body
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


	def visit_Import(self, node):
		def _import_as_name(self, node, name, asname):
			ref = asname.hl.scope
			assert ref is not None
			assert ref.modtype != MelanoModule.PROJECT
			tgt = self.visit(asname)
			self.comment("Import module {} as {}".format(str(name), str(asname)))
			tmp = PyObjectType(self.scope.context.tmpname())
			tmp.declare(self.scope.context)
			self.context.add(c.Assignment('=', c.ID(tmp.name), c.FuncCall(c.ID('PyImport_ImportModule'), c.ExprList(
																												c.Constant('string', str(name))))))
			tmp.fail_if_null(self.context, tmp.name)
			self._store(asname, tgt, tmp)

		def _import(self, node, name):
			ref = name.hl.scope
			assert ref is not None
			assert ref.modtype != MelanoModule.PROJECT
			tgt = self.visit(name)
			self.comment("Import module {}".format(str(name)))
			tmp = PyObjectType(self.scope.context.tmpname())
			tmp.declare(self.scope.context)
			self.context.add(c.Assignment('=', c.ID(tmp.name), c.FuncCall(c.ID('PyImport_ImportModule'), c.ExprList(
																												c.Constant('string', str(name))))))
			tmp.fail_if_null(self.context, tmp.name)

			#NOTE: if we are importing from an attribute, we also need to import the goal name, so it exists, _and_ we 
			#		need to import the base name so that we can assign it to the target name
			if isinstance(name, py.Attribute):
				basename = str(name.first())
				self.context.add(c.Assignment('=', c.ID(tmp.name), c.FuncCall(c.ID('PyImport_ImportModule'), c.ExprList(
																													c.Constant('string', str(basename))))))
				tmp.fail_if_null(self.context, tmp.name)
				self._store(name.first(), tgt, tmp)
			else:
				self._store(name, tgt, tmp)

		for alias in node.names:
			if alias.asname:
				_import_as_name(self, node, alias.name, alias.asname)
			else:
				_import(self, node, alias.name)




	def visit_ImportFrom(self, node):
		# import the module
		modname = '.' * node.level + str(node.module)
		tmp = PyObjectType(self.scope.context.tmpname())
		tmp.declare(self.scope.context)
		self.context.add(c.Assignment('=', c.ID(tmp.name), c.FuncCall(c.ID('PyImport_ImportModule'), c.ExprList(
																											c.Constant('string', str(modname))))))
		tmp.fail_if_null(self.context, tmp.name)

		for alias in node.names:
			name = str(alias.name)
			if name == '*':
				raise NotImplementedError

			# load the name off of the module
			val = PyObjectType(self.scope.context.tmpname())
			val.declare(self.scope.context)
			self.context.add(c.Assignment('=', c.ID(val.name), c.FuncCall(c.ID('PyObject_GetAttrString'), c.ExprList(
																		c.ID(tmp.name), c.Constant('string', name)))))
			val.fail_if_null(self.context, val.name)
			if alias.asname:
				tgt = self.visit(alias.asname)
				self._store(alias.asname, tgt, val)
			else:
				tgt = self.visit(alias.name)
				self._store(alias.name, tgt, val)


	def visit_Name(self, node):
		# if we are storing to the name, we just need to return the instance, so we can assign to it
		if node.ctx == py.Store or node.ctx == py.Param:
			#NOTE: names will not get out of sync here because they share the same underlying Name, so the rename
			#		happens for all shared names in a Scope.
			if not node.hl.inst:
				node.hl.ll_name = self.scope.context.reserve_name(node.hl.ll_name, node.hl, self.tu)
				node.hl.create_instance(node.hl.ll_name)
				node.hl.inst.declare(self.scope.context)
			return node.hl.inst

		# if we are loading a name, we have to search for the name's location
		elif node.ctx == py.Load:
			return self._load(node)
			'''
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
				inst = PyObjectType(tmp)
				inst.declare(self.scope.context)

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
				inst.fail_if_null(self.context, tmp)

				return inst
			else:
				#For higher non-local scopes, we can access the scope dict directly
				assert scope.has_name(name)
				tmp = self.scope.context.tmpname()
				inst = node.hl.get_type()(tmp)
				inst.declare(self.scope.context)
				scope.inst.get_item_string(self.context, name, inst)
				if node.hl.inst is None:
					node.hl.inst = inst

			return node.hl.inst
			'''


	def visit_Num(self, node):
		node.hl.create_instance(self.scope.context.tmpname())
		node.hl.inst.declare(self.scope.context)
		node.hl.inst.new(self.context, node.n)
		return node.hl.inst


	def visit_Raise(self, node):
		#FIXME: re-raise existing context if node.exc is not present

		inst = self.visit(node.exc)
		'''
		if(PyObject_IsInstance(inst.name, PyType_Type)) {
			PyErr_SetObject(inst.name, ??);
		} else {
			PyErr_SetObject(PyObject_Type(inst.name), inst.name);
		}
		goto end;
		'''
		is_a_type = inst.is_instance(self.context, c.Cast(c.PtrDecl(c.TypeDecl(None, c.IdentifierType('PyObject'))), c.UnaryOp('&', c.ID('PyType_Type'))))
		if_stmt = c.If(c.ID(is_a_type.name), c.Compound(), c.Compound())
		with self.new_context(if_stmt.iftrue):
			self.context.add(c.FuncCall(c.ID('PyErr_SetObject'), c.ExprList(c.ID(inst.name), c.ID('NULL'))))
		with self.new_context(if_stmt.iffalse):
			ty_inst = PyTypeType(self.scope.context.tmpname())
			ty_inst.declare(self.scope.context)
			inst.get_type(self.context, ty_inst)
			self.context.add(c.FuncCall(c.ID('PyErr_SetObject'), c.ExprList(c.ID(ty_inst.name), c.ID(inst.name))))
		self.context.add(LLType.capture_error(self.context))
		self.context.add(if_stmt)
		self.context.add(c.Goto('end'))


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
		node.hl.create_instance(self.scope.context.tmpname())
		node.hl.inst.declare(self.scope.context)
		node.hl.inst.new(self.context, PyStringType.str2c(node.s))
		return node.hl.inst


	def visit_Tuple(self, node):
		node.hl.create_instance(self.scope.context.tmpname())
		node.hl.inst.declare(self.scope.context)
		to_pack = []
		if node.elts:
			for n in node.elts:
				inst = self.visit(n)
				inst.incref(self.context)
				to_pack.append(inst)
		node.hl.inst.pack(self.context, *to_pack)
		return node.hl.inst
	visit_List = visit_Tuple


	def visit_With(self, node):
		ctx = self.visit(node.context_expr)

		ent = PyObjectType(self.scope.context.tmpname())
		ent.declare(self.scope.context)
		ext = PyObjectType(self.scope.context.tmpname())
		ext.declare(self.scope.context)
		tmp = PyObjectType(self.scope.context.tmpname())
		tmp.declare(self.scope.context)

		ctx.get_attr_string(self.context, '__exit__', ext)

		ctx.get_attr_string(self.context, '__enter__', ent)
		args = PyTupleType(self.scope.context.tmpname())
		args.declare(self.scope.context)
		args.pack(self.context)
		ent.call(self.context, args, None, tmp)

		if node.optional_vars:
			var = self.visit(node.optional_vars)
			self._store(node.optional_vars, var, tmp)

		if isinstance(node.body, list):
			self.visit_nodelist(node.body)
		else:
			self.visit(node.body)

		###FIXME: how do we ensure finally?
		#TODO: Check for exception
		#if an exception was raised:
		#	exc = copy of (exception, instance, traceback)
		#else:
		#	exc = (None, None, None)
		#exit(*exc)
		args = PyTupleType(self.scope.context.tmpname())
		args.declare(self.scope.context)
		args.pack(self.context, None, None, None)
		out_var = PyObjectType(self.scope.context.tmpname())
		out_var.declare(self.scope.context)
		ext.call(self.context, args, None, out_var)


	def visit_UnaryOp(self, node):
		o = self.visit(node.operand)

		if not node.hl.inst:
			node.hl.create_instance(self.scope.context.tmpname())
			node.hl.inst.declare(self.scope.context)

		if node.op == py.Invert:
			o.invert(self.context, node.hl.inst)
		elif node.op == py.Not:
			o.not_(self.context, node.hl.inst)
		elif node.op == py.UAdd:
			o.positive(self.context, node.hl.inst)
		elif node.op == py.USub:
			o.negative(self.context, node.hl.inst)
		else:
			raise NotImplementedError("UnaryOp({})".format(node.op))

		return node.hl.inst
