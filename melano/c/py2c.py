'''
Copyright (c) 2011, Terrence Cole.
All rights reserved.
'''
from . import ast as c
from contextlib import contextmanager
from melano.c.pybuiltins import PY_BUILTINS
from melano.c.types.integer import CIntegerLL
from melano.c.types.lltype import LLType
from melano.c.types.pybool import PyBoolLL
from melano.c.types.pybytes import PyBytesLL
from melano.c.types.pycfunction import PyCFunctionLL
from melano.c.types.pydict import PyDictLL
from melano.c.types.pyfloat import PyFloatLL
from melano.c.types.pyinteger import PyIntegerLL
from melano.c.types.pylist import PyListLL
from melano.c.types.pymodule import PyModuleLL
from melano.c.types.pyobject import PyObjectLL
from melano.c.types.pyset import PySetLL
from melano.c.types.pystring import PyStringLL
from melano.c.types.pytuple import PyTupleLL
from melano.c.types.pytype import PyTypeLL
from melano.hl.module import MelanoModule
from melano.hl.types.hltype import HLType
from melano.hl.types.integer import CIntegerType
from melano.hl.types.pybool import PyBoolType
from melano.hl.types.pybytes import PyBytesType
from melano.hl.types.pydict import PyDictType
from melano.hl.types.pyfloat import PyFloatType
from melano.hl.types.pyfunction import PyFunctionType
from melano.hl.types.pyinteger import PyIntegerType
from melano.hl.types.pylist import PyListType
from melano.hl.types.pymodule import PyModuleType
from melano.hl.types.pyobject import PyObjectType
from melano.hl.types.pyset import PySetType
from melano.hl.types.pystring import PyStringType
from melano.hl.types.pytuple import PyTupleType
from melano.lang.visitor import ASTVisitor
from melano.py import ast as py
import itertools
import pdb
import tc

HLType


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
	TYPEMAP = {
		PyObjectType: PyObjectLL,
		PyModuleType: PyModuleLL,
		PyFunctionType: PyCFunctionLL,
		PyBoolType: PyBoolLL,
		PyBytesType: PyBytesLL,
		PyDictType: PyDictLL,
		PyFloatType: PyFloatLL,
		PyIntegerType: PyIntegerLL,
		PyListType: PyListLL,
		PySetType: PySetLL,
		PyStringType: PyStringLL,
		PyTupleType: PyTupleLL,
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
		self.tu.add_include(c.Comment(' ***Includes*** '))
		self.tu.add_include(c.Include('Python.h', True))
		self.tu.add_include(c.Include('data/c/env.h', False))

		# add common names
		self.tu.reserve_name('builtins')
		self.tu.reserve_name('None')
		self.tu.add_fwddecl(c.Comment(' ***Global Vars*** '))
		self.tu.add_fwddecl(c.Decl('builtins', c.PtrDecl(c.TypeDecl('builtins', c.IdentifierType('PyObject'))), ['static']))
		self.tu.add_fwddecl(c.Decl('None', c.PtrDecl(c.TypeDecl('None', c.IdentifierType('PyObject'))), ['static']))

		# the main function -- handles init, cleanup, and error printing at top level
		self.tu.reserve_name('main')
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
					c.Assignment('=', c.ID('builtins'), c.FuncCall(c.ID('PyImport_ImportModule'), c.ExprList(c.Constant('string', 'builtins')))),
					c.Assignment('=', c.ID('None'), c.FuncCall(c.ID('PyObject_GetAttrString'), c.ExprList(c.ID('builtins'), c.Constant('string', 'None')))),
			)
		)
		self.tu.add_fwddecl(self.main.decl)
		self.tu.add(c.Comment(' ***Entry Point*** '))
		self.tu.add(self.main)

		# the low-level statment emission context... e.g. the Compound for functions, ifs, etc.
		self.context = self.main.body
		self.context._visitor = self

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
		ctx._tu = self.tu

		prior = self.context
		self.context = ctx
		yield
		self.context = prior


	@contextmanager
	def module_scope(self):
		'''Set the scope and context as the module scope/context, no matter what function we are processing.
			We use this to declare functions, classes etc all at module build time, even nested function/classes.'''
		prior_scopes = self.scopes
		prior_context = self.context
		self.scopes = [self.hl_module]
		self.context = self.ll_module.c_builder_func.body
		self.context._visitor = self
		self.context._tu = self.tu
		yield
		self.scopes = prior_scopes
		self.context = prior_context


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


	def create_ll_instance(self, hlnode:HLType):
		inst = self.TYPEMAP[hlnode.get_type().__class__](hlnode)
		hlnode.ll = inst
		return inst


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
			if isinstance(target, py.Attribute):
				o = self.visit(target.value)
				o.set_attr_string(self.context, str(target.attr), val)
			elif isinstance(target, py.Subscript):
				o = self.visit(target.value)
				i = self.visit(target.slice)
				o.set_item(self.context, i, val)
			elif isinstance(target, py.Name):
				tgt = self.visit(target)
				self._store(target, val)
			else:
				raise NotImplementedError("Don't know how to assign to type: {}".format(type(target)))


	def visit_Index(self, node):
		#NOTE: Pass through index values... not sure why python ast wraps these rather than just having a value.
		node.hl = node.value.hl
		node.hl.ll = self.visit(node.value)
		return node.hl.ll


	def _store(self, target, val):
		'''
		Common "normal" assignment handler.  Things like for-loop targets and with-stmt vars 
			need the same full suite of potential assignment targets as normal assignments.  With
			the caveat that only assignment will have non-Name children.
		
		target -- the node that is the lhs of the storage.
		'''
		assert isinstance(target, py.Name)

		# NOTE: the hl Name or Ref will always be parented under  the right scope
		scope = target.hl.parent
		scope.ll.set_attr_string(self.context, str(target), val)

		#TODO: destructuring assignment
		#target.hl.parent.inst.set_item_string(self.context, str(target), val)

		#TODO: this is an optimization; we only want to do it when we can get away with it, and when we can
		#		get away with it, we don't want to assign to the namespace.
		#if tgt:
		#	tgt.assign_name(self.context, val)



	def _load(self, source):
		'''
		source - the underlying name reference that we need to provide access to
		'''
		tmp = PyObjectLL(None)
		tmp.declare(self.scope.context)

		# if we have a scope, load from it
		if source.hl.parent.ll:
			source.hl.parent.ll.get_attr_string(self.context, str(source), tmp)
		# otherwise, load from the global scope
		else:
			self.ll_module.get_attr_string(self.context, str(source), tmp)
		return tmp


	def visit_Attribute(self, node):
		if node.ctx == py.Store:
			# load the lhs object into the local c scope
			if isinstance(node.value, py.Name):
				lhs = self._load(node.value)
			else:
				lhs = self.visit(node.value)

			# load the attr off of the lhs, for use as a storage target
			inst = PyObjectLL(None)
			inst.declare(self.scope.context)
			lhs.get_attr_string(self.context, str(node.attr), inst)
			return inst

		elif node.ctx == py.Load:
			# load the attr lhs as normal
			inst = self.visit(node.value)
			self.comment('Load Attribute "{}.{}"'.format(str(node.value), str(node.attr)))

			# store the attr value into a local tmp variable
			tmp = PyObjectLL(None)
			tmp.declare(self.scope.context)
			inst.get_attr_string(self.context, str(node.attr), tmp)
			return tmp

		else:
			raise NotImplementedError("Unknown Attribute access context: {}".format(node.ctx))


	def visit_Subscript(self, node):
		if node.ctx == py.Store:
			raise NotImplementedError("Subscript store needs special casing at assignment site")

		elif node.ctx == py.Load:
			kinst = self.visit(node.slice)
			tgtinst = self.visit(node.value)
			tmp = PyObjectLL(None)
			tmp.declare(self.scope.context)
			tgtinst.get_item(self.context, kinst, tmp)
			return tmp
		else:
			raise NotImplementedError("Unknown Attribute access context: {}".format(node.ctx))


	def visit_BinOp(self, node):
		l = self.visit(node.left)
		r = self.visit(node.right)

		inst = self.create_ll_instance(node.hl)
		inst.declare(self.context)

		#TODO: python detects str + str at runtime and skips dispatch through PyNumber_Add, so we can 
		#		assume that would be faster
		if node.op == py.BitOr:
			l.bitor(self.context, r, inst)
		elif node.op == py.BitXor:
			l.bitxor(self.context, r, inst)
		elif node.op == py.BitAnd:
			l.bitand(self.context, r, inst)
		elif node.op == py.LShift:
			l.lshift(self.context, r, inst)
		elif node.op == py.RShift:
			l.rshift(self.context, r, inst)
		elif node.op == py.Add:
			l.add(self.context, r, inst)
		elif node.op == py.Sub:
			l.subtract(self.context, r, inst)
		elif node.op == py.Mult:
			l.multiply(self.context, r, inst)
		elif node.op == py.Div:
			l.divide(self.context, r, inst)
		elif node.op == py.FloorDiv:
			l.floor_divide(self.context, r, inst)
		elif node.op == py.Mod:
			l.modulus(self.context, r, inst)
		elif node.op == py.Pow:
			l.power(self.context, r, inst)
		else:
			raise NotImplementedError("BinOp({})".format(node.op))

		return inst


	def visit_Call(self, node):
		def _call_remote(self, node, funcinst):
			# build the arg tuple
			args_insts = []
			if node.args:
				for arg in node.args:
					idinst = self.visit(arg)
					idinst = idinst.as_pyobject(self.context)
					args_insts.append(idinst)
				for idinst in args_insts:
					# pytuple pack will steal the ref, but we want to be able to cleanup the node later
					# note: do this after visiting all other nodes to minimize our probability of leaking the extra ref
					#FIXME: make it possible for a failure in the tuple packing to free these refs?  Or is this a bad idea
					#		because a failure halfway through would end up with us double-freeing half of our refs?
					idinst.incref(self.context)
			# Note: we always need to pass a tuple as args, even if there is nothing in it
			args1 = PyTupleLL(None)
			args1.declare(self.scope.context)
			args1.pack(self.context, *args_insts)

			# build the keyword dict
			args2 = None
			if node.keywords:
				kw_insts = []
				for kw in node.keywords:
					valinst = self.visit(kw.value)
					valinst = valinst.as_pyobject(self.context)
					kw_insts.append((str(kw.keyword), valinst))
				if kw_insts:
					args2 = PyDictLL(None)
					args2.declare(self.scope.context)
					args2.new(self.context)
					for keyname, valinst in kw_insts:
						args2.set_item_string(self.context, keyname, valinst)

			# begin call output
			self.comment('Call function "{}"'.format(str(node.func)))

			# build the output variable
			rv = PyObjectLL(None)
			rv.declare(self.scope.context)

			# make the call
			funcinst.call(self.context, args1, args2, rv)

			# cleanup the args
			args1.delete(self.context)
			if args2: args2.delete(self.context)

			return rv


		#TODO: direct calling, keywords calling, etc
		#TODO: track "type" so we can dispatch to PyCFunction_Call or PyFunction_Call instead of PyObject_Call 
		#TODO: track all call methods (callsite usage types) and see if we can't unpack into a direct c call

		# prepare the func name node
		funcinst = self.visit(node.func)

		# if we are defined locally, we can know the expected calling proc and reorganize our args to it
		#if node.func.hl and node.func.hl.scope:
		#	return _call_local(self, node, funcinst)
		#else:
		#	return _call_remote(self, node, funcinst)
		return _call_remote(self, node, funcinst)

		'''			
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
		args1 = PyTupleLL(None)
		args1.declare(self.scope.context)
		args1.pack(self.context, *args_insts)
		'''

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

		'''
		# begin call output
		self.comment('Call function "{}"'.format(str(node.func)))

		# build the output variable
		rv = PyObjectLL(None)
		rv.declare(self.scope.context)

		# make the call
		funcinst.call(self.context, args1, None, rv)

		# cleanup the args
		args1.delete(self.context)
		#if kw_args: kw_args.delete(self.context)

		return rv
		'''


	def visit_Compare(self, node):
		# format and print the op we are doing for sanity sake
		s = 'Compare ' + str(node.left)
		for o, b in zip(node.ops, node.comparators):
			s += ' {} {}'.format(self.COMPARATORS_PRETTY[o], str(b))
		self.comment(s)

		# initialize new tmp variable with default value of false
		out = CIntegerLL(None, is_a_bool=True)
		out.declare(self.scope.context, init=0)

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
		inst = self.create_ll_instance(node.hl)
		inst.declare(self.scope.context)
		inst.new(self.context)
		if node.keys and node.values:
			for k, v in zip(node.keys, node.values):
				kinst = self.visit(k)
				vinst = self.visit(v)
				inst.set_item(self.context, kinst, vinst)
		return inst


	def visit_For(self, node):
		#for <target> in <iter>: <body>
		#else: <orelse>

		#TODO: for:else/break

		tgt = self.visit(node.target)
		iter_obj = self.visit(node.iter)

		# get the PyIter for the iteration object
		iter = PyObjectLL(None)
		iter.declare(self.scope.context)
		iter_obj.get_iter(self.context, iter)

		# the gets the object locally inside of the while expr; we do the full assignment inside the body
		tmp = PyObjectLL(None)
		tmp.declare(self.scope.context)
		stmt = c.While(c.Assignment('=', c.ID(tmp.name), c.FuncCall(c.ID('PyIter_Next'), c.ExprList(c.ID(iter.name)))), c.Compound())
		self.context.add(stmt)
		with self.new_context(stmt.stmt):
			self._store(node.target, tmp)
			self.visit_nodelist(node.body)


	def visit_FunctionDef(self, node):
		#FIXME: PyCFunction cannot take an attr for __defaults__, __kwdefaults__, or __annotations__!?!
		#TODO: do we want to do cleanup of our locals dicts in main before PyFinalize()?

		# declare
		docstring, body = self.split_docstring(node.body)
		inst = self.create_ll_instance(node.hl)
		inst.create_locals(self.tu)
		if node.args.defaults:
			inst.create_defaults(self.tu, len(node.args.defaults))
		if node.args.kw_defaults:
			inst.create_kwdefaults(self.tu, len(node.args.kw_defaults))
		#inst.create_annotations(self.tu)
		inst.create_pystubfunc(self.tu)

		# the runner func needs the full param list
		inst.create_runnerfunc(self.tu, node.args.args or [], node.args.vararg, node.args.kwonlyargs or [], node.args.kwarg)

		# NOTE: we create _all_ functions, even nested/class functions, in the module, instead of their surrounding scope
		#		so that we don't have to re-create the full infrastructure every time we visit the outer scope
		with self.module_scope():
			self.comment("Build function {}".format(str(node.name)))
			pycfunc = inst.create_funcdef(self.context, self.tu, docstring)

			# attach defaults to the pycfunction instance
			if node.args.defaults:
				for i, default in enumerate(node.args.defaults):
					default_inst = self.visit(default)
					self.context.add(c.Assignment('=', c.ArrayRef(inst.c_defaults_name, i), c.ID(default_inst.name)))

			# attach kwonly defaults to the pycfunction instance
			if node.args.kw_defaults:
				for i, default in enumerate(node.args.kw_defaults):
					default_inst = self.visit(default)
					self.context.add(c.Assignment('=', c.ArrayRef(inst.c_kwdefaults_name, i), c.ID(default_inst.name)))

			# attach annotations to the pycfunction instance

		# Build the python stub function
		with self.new_scope(node.hl, inst.c_pystub_func.body):
			# Attach all parameters and names into the local namespace
			# We can't know the convention the caller used, so we need to handle all 
			#  possiblities -- local callers do their own setup and just call the runner.
			self.context.reserve_name('self')

			self.context.reserve_name('args')
			args_tuple = PyTupleLL(None)
			args_tuple.name = 'args'

			self.context.reserve_name('kwargs')
			kwargs_dict = PyDictLL(None)
			kwargs_dict.name = 'kwargs'

			self.comment('Python interface stub function "{}"'.format(str(node.name)))
			inst.stub_intro(self.context)

			# load positional and normal keyword args
			if node.args.args:
				c_args_size = CIntegerLL(None)
				c_args_size.declare(self.scope.context, name='args_size')
				args_tuple.get_size_unchecked(self.context, c_args_size)
				arg_insts = [None] * len(node.args.args)
				for i, arg in enumerate(node.args.args):
					# declare local variable for arg ref
					arg_insts[i] = self.create_ll_instance(arg.arg.hl)
					arg_insts[i].declare(self.scope.context)

					# query if in positional args
					self.comment("Grab arg {}".format(str(arg.arg)))
					query_inst = c.If(c.BinaryOp('>', c.ID(c_args_size.name), c.Constant('integer', i)),
										c.Compound(), c.Compound())
					self.context.add(query_inst)

					# get the positional arg
					with self.new_context(query_inst.iftrue):
						args_tuple.get_unchecked(self.context, i, arg_insts[i])

					# get the keyword arg
					with self.new_context(query_inst.iffalse):
						have_kwarg = c.If(c.ID('kwargs'), c.Compound(), None)
						self.context.add(have_kwarg)
						with self.new_context(have_kwarg.iftrue):
							kwargs_dict.get_item_string_nofail(self.context, str(arg.arg), arg_insts[i])

						query_default_inst = c.If(c.UnaryOp('!', c.ID(arg_insts[i].name)), c.Compound(), None)
						self.context.add(query_default_inst)
						# try loading from defaults
						with self.new_context(query_default_inst.iftrue):
							#TODO: only get the defaults / kwdefaults once
							kwstartoffset = len(node.args.args) - len(node.args.defaults)
							if i >= kwstartoffset:
								default_offset = i - kwstartoffset
								self.context.add(c.Assignment('=', c.ID(arg_insts[i].name), c.ArrayRef(inst.c_defaults_name, default_offset)))
							else:
								# emit an error for an unpassed arg
								PyObjectLL.fail(self.context, 'Missing arg {}'.format(str(arg)))

				# check if we have extra args remaining that need to go into varargs and kwargs
				#have_extra_args = c.If(c.BinaryOp('>', c.ID(c_args_size.name), c.Constant('integer', len(node.args.args))))
				#self.context.add(have_extra_args)
				#with self.new_context(have_extra_args.iftrue):
				#	# collect 
				#
				#	varargs_inst = PyListLL(None)
				#	args_tuple.slice(


			# load all keyword only args
			#		PyObjectLL.fail(self.context, 'Require kwargs for function with kwonlyargs')
			if node.args.kwonlyargs:
				kwarg_insts = [None] * len(node.args.kwonlyargs)
				for i, arg in enumerate(node.args.kwonlyargs):
					kwarg_insts[i] = self.create_ll_instance(arg.arg.hl)
					kwarg_insts[i].declare(self.scope.context)

				# ensure we have kwargs at all
				have_kwarg = c.If(c.ID('kwargs'), c.Compound(), c.Compound())
				self.context.add(have_kwarg)
				with self.new_context(have_kwarg.iftrue):
					# load all kwarg insts
					for i, arg in enumerate(node.args.kwonlyargs):
						kwargs_dict.get_item_string_nofail(self.context, str(arg.arg), kwarg_insts[i])
						need_default = c.If(c.UnaryOp('!', c.ID(kwarg_insts[i].name)), c.Compound(), None)
						self.context.add(need_default)
						with self.new_context(need_default.iftrue):
							self.context.add(c.Assignment('=', c.ID(kwarg_insts[i].name), c.ArrayRef(inst.c_kwdefaults_name, i)))
				with self.new_context(have_kwarg.iffalse):
					for i, arg in enumerate(node.args.kwonlyargs):
						self.context.add(c.Assignment('=', c.ID(kwarg_insts[i].name), c.ArrayRef(inst.c_kwdefaults_name, i)))

			#TODO: add unused args to varargs and pass if needed or error if not
			#TODO: add unused kwargs to varargs and pass if needed or error if not

			# call the runner func
			inst.call_runnerfunc(self.context, node.args.args or [], node.args.vararg, node.args.kwonlyargs or [], node.args.kwarg)
			with self.new_scope(self.scope, inst.c_runner_func.body):
				inst.runner_intro(self.context)

				# attach args to locals
				for i, arg in enumerate(node.args.args or []):
					inst.set_attr_string(self.context, str(arg.arg), arg_insts[i])
				for i, arg in enumerate(node.args.kwonlyargs or []):
					inst.set_attr_string(self.context, str(arg.arg), kwarg_insts[i])

				self.visit_nodelist(node.body)
				inst.runner_outro(self.context)

			# emit cleanup and return code
			inst.stub_outro(self.context)

		self._store(node.name, pycfunc)

		return inst


	def visit_If(self, node):
		inst = self.visit(node.test)
		if isinstance(inst, PyObjectLL):
			tmpvar = inst.is_true(self.context)
			test = c.BinaryOp('==', c.Constant('integer', 1), c.ID(tmpvar))
		elif isinstance(inst, CIntegerLL):
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
			tmp = PyObjectLL(None)
			tmp.declare(self.scope.context)
			self.context.add(c.Assignment('=', c.ID(tmp.name), c.FuncCall(c.ID('PyImport_ImportModule'), c.ExprList(
																												c.Constant('string', str(name))))))
			tmp.fail_if_null(self.context, tmp.name)
			self._store(asname, tmp)

		def _import(self, node, name):
			if isinstance(name, py.Name):
				ref = name.hl.scope
				tgt = self.visit(name)
			else:
				assert isinstance(name, py.Attribute)
				ref = name.first().hl.scope
				tgt = self.visit(name.first())

			assert ref is not None
			#FIXME: need to implement in-project imports
			#assert ref.modtype != MelanoModule.PROJECT

			self.comment("Import module {}".format(str(name)))
			tmp = PyObjectLL(None)
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
				self._store(name.first(), tmp)
			else:
				self._store(name, tmp)

		for alias in node.names:
			if alias.asname:
				_import_as_name(self, node, alias.name, alias.asname)
			else:
				_import(self, node, alias.name)




	def visit_ImportFrom(self, node):
		# import the module
		modname = '.' * node.level + str(node.module)
		tmp = PyObjectLL(None)
		tmp.declare(self.scope.context)
		self.context.add(c.Assignment('=', c.ID(tmp.name), c.FuncCall(c.ID('PyImport_ImportModule'), c.ExprList(
																											c.Constant('string', str(modname))))))
		tmp.fail_if_null(self.context, tmp.name)

		for alias in node.names:
			name = str(alias.name)
			if name == '*':
				raise NotImplementedError

			# load the name off of the module
			val = PyObjectLL(None)
			val.declare(self.scope.context)
			self.context.add(c.Assignment('=', c.ID(val.name), c.FuncCall(c.ID('PyObject_GetAttrString'), c.ExprList(
																		c.ID(tmp.name), c.Constant('string', name)))))
			val.fail_if_null(self.context, val.name)
			if alias.asname:
				tgt = self.visit(alias.asname)
				self._store(alias.asname, val)
			else:
				tgt = self.visit(alias.name)
				self._store(alias.name, val)


	def visit_Module(self, node):
		# we need the toplevel available to all children so that we can do lookups for globals
		self.hl_module = node.hl
		self.ll_module = self.create_ll_instance(self.hl_module)

		# setup the module
		self.ll_module.declare(self.tu)

		# set the initial context
		with self.new_context(self.ll_module.c_builder_func.body):
			# setup the module
			self.ll_module.return_existing(self.context)
			self.comment('Create module "{}" as "{}"'.format(self.hl_module.name, self.hl_module.owner.name))
			self.ll_module.new(self.context)
			self.ll_module.get_dict(self.context)

			# load and attach special attributes to the module dict
			self.ll_module.set_initial_string_attribute(self.context, '__name__', self.hl_module.owner.name)
			self.ll_module.set_initial_string_attribute(self.context, '__file__', self.hl_module.filename)
			docstring, body = self.split_docstring(node.body)
			self.ll_module.set_initial_string_attribute(self.context, '__doc__', docstring)

			# visit all children
			with self.global_scope(self.hl_module):
				# record the top-level context in the scope, so we can declare toplevel variables when in a sub-contexts
				self.scope.context = self.context

				# visit all children
				self.visit_nodelist(body)

			# cleanup and return
			self.ll_module.emit_outro(self.context)

		# add the function call to the main to set the module's global name
		#FIXME: this will load all modules at startup time, and only fetch existing references at runtime... this is a fairly
		#		significant change from standard python, and i should probably think of a way to fix it.
		tmp = self.main.body.tmp_pyobject()
		self.main.body.add(c.Assignment('=', c.ID(tmp), c.FuncCall(c.ID(self.ll_module.c_builder_name), c.ExprList())))
		self.main.body.add(c.If(c.UnaryOp('!', c.ID(tmp)), c.Compound(
								c.FuncCall(c.ID('__err_show_traceback__'), c.ExprList()),
								c.FuncCall(c.ID('PyErr_Print'), c.ExprList()),
								c.Return(c.Constant('integer', 1),
							)), None))

		return self.ll_module


	def visit_Name(self, node):
		# if we are storing to the name, we just need to return the instance, so we can assign to it
		if node.ctx == py.Store or node.ctx == py.Param:
			if not node.hl.ll:
				inst = self.create_ll_instance(node.hl)
				inst.declare(self.scope.context)
			return node.hl.ll

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
		inst = self.create_ll_instance(node.hl)
		inst.declare(self.scope.context)
		inst.new(self.context, node.n)
		return inst


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
			ty_inst = PyTypeLL(None)
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


	def visit_Set(self, node):
		inst = self.create_ll_instance(node.hl)
		inst.declare(self.scope.context)
		inst.new(self.context, None)
		for v in node.elts:
			vinst = self.visit(v)
			inst.add(self.context, vinst)
		return inst


	def visit_Str(self, node):
		inst = self.create_ll_instance(node.hl)
		inst.declare(self.scope.context)
		inst.new(self.context, PyStringLL.str2c(node.s))
		return inst


	def visit_Tuple(self, node):
		inst = self.create_ll_instance(node.hl)
		inst.declare(self.scope.context)
		to_pack = []
		if node.elts:
			for n in node.elts:
				e_inst = self.visit(n)
				to_pack.append(e_inst)
		for e_inst in to_pack:
			e_inst.incref(self.context)
		inst.pack(self.context, *to_pack)
		return node.hl.ll
	visit_List = visit_Tuple


	def visit_With(self, node):
		ctx = self.visit(node.context_expr)

		ent = PyObjectLL(None)
		ent.declare(self.scope.context)
		ext = PyObjectLL(None)
		ext.declare(self.scope.context)
		tmp = PyObjectLL(None)
		tmp.declare(self.scope.context)

		ctx.get_attr_string(self.context, '__exit__', ext)

		ctx.get_attr_string(self.context, '__enter__', ent)
		args = PyTupleLL(None)
		args.declare(self.scope.context)
		args.pack(self.context)
		ent.call(self.context, args, None, tmp)

		if node.optional_vars:
			var = self.visit(node.optional_vars)
			self._store(node.optional_vars, tmp)

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
		args = PyTupleLL(None)
		args.declare(self.scope.context)
		args.pack(self.context, None, None, None)
		out_var = PyObjectLL(None)
		out_var.declare(self.scope.context)
		ext.call(self.context, args, None, out_var)


	def visit_UnaryOp(self, node):
		o = self.visit(node.operand)

		inst = PyObjectLL(None)
		inst.declare(self.scope.context)

		if node.op == py.Invert:
			o.invert(self.context, inst)
		elif node.op == py.Not:
			o.not_(self.context, inst)
		elif node.op == py.UAdd:
			o.positive(self.context, inst)
		elif node.op == py.USub:
			o.negative(self.context, inst)
		else:
			raise NotImplementedError("UnaryOp({})".format(node.op))

		return inst
