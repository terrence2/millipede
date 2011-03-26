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
from melano.c.types.pyclass import PyClassLL
from melano.c.types.pyclosure import PyClosureLL
from melano.c.types.pycomprehension import PyComprehensionLL
from melano.c.types.pydict import PyDictLL
from melano.c.types.pyfloat import PyFloatLL
from melano.c.types.pyfunction import PyFunctionLL
from melano.c.types.pygenerator import PyGeneratorLL
from melano.c.types.pygeneratorclosure import PyGeneratorClosureLL
from melano.c.types.pyinteger import PyIntegerLL
from melano.c.types.pylist import PyListLL
from melano.c.types.pymodule import PyModuleLL
from melano.c.types.pyobject import PyObjectLL
from melano.c.types.pyset import PySetLL
from melano.c.types.pystring import PyStringLL
from melano.c.types.pytuple import PyTupleLL
from melano.c.types.pytype import PyTypeLL
from melano.hl.class_ import MelanoClass
from melano.hl.function import MelanoFunction
from melano.hl.module import MelanoModule
from melano.hl.types.hltype import HLType
from melano.hl.types.integer import CIntegerType
from melano.hl.types.pybool import PyBoolType
from melano.hl.types.pybytes import PyBytesType
from melano.hl.types.pyclass import PyClassType
from melano.hl.types.pyclosure import PyClosureType
from melano.hl.types.pycomprehension import PyComprehensionType
from melano.hl.types.pydict import PyDictType
from melano.hl.types.pyfloat import PyFloatType
from melano.hl.types.pyfunction import PyFunctionType
from melano.hl.types.pygenerator import PyGeneratorType
from melano.hl.types.pygeneratorclosure import PyGeneratorClosureType
from melano.hl.types.pyinteger import PyIntegerType
from melano.hl.types.pylist import PyListType
from melano.hl.types.pymodule import PyModuleType
from melano.hl.types.pyobject import PyObjectType
from melano.hl.types.pyset import PySetType
from melano.hl.types.pystring import PyStringType
from melano.hl.types.pytuple import PyTupleType
from melano.lang.visitor import ASTVisitor
from melano.py import ast as py
from tc import Nonable
import itertools
import pdb
import tc

class InvalidScope(Exception):
	'''Raised when a keyword or operation appears in a place where it should not appear.'''


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
	BOOLOPS_PRETTY = {
		py.And: 'and',
		py.Or: 'or'
	}
	AUGASSIGN_PRETTY = {
		py.BitOr: '|=',
		py.BitXor: '^=',
		py.BitAnd: '&=',
		py.LShift: '<<=',
		py.RShift: '>>=',
		py.Add: '+=',
		py.Sub: '-=',
		py.Mult: '*=',
		py.Div: '/=',
		py.FloorDiv: '//=',
		py.Mod: '%=',
		py.Pow: '**=',
	}
	TYPEMAP = {
		PyObjectType: PyObjectLL,
		PyModuleType: PyModuleLL,
		PyFunctionType: PyFunctionLL,
		PyGeneratorType: PyGeneratorLL,
		PyClosureType: PyClosureLL,
		PyGeneratorClosureType: PyGeneratorClosureLL,
		PyComprehensionType: PyComprehensionLL,
		PyClassType: PyClassLL,
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

		# There are a number of constructs that change the flow of control in python in ways that are not directly
		# 		representable in c without goto.  We use the flow-control list to allow constructs that change the flow of
		#		control to work together to create a correct goto-web.
		self.flowcontrol = []

		# A) If we get an exception from within an exception handling context, we need to
		#	(1) trigger a nested exception output in our traceback line list
		# -- i think this is all -- the new exception appears to stomp the old exception in libpython
		#	TODO -- does python track multiple exceptions internally or does it rely on traceback inspection to recreate this info?
		#	B) Also, if we have a bare raise in an exception handler, we need to know what exception to raise.
		self.exc_cookie_stack = []

		# the main unit where we put top-level entries
		self.tu = c.TranslationUnit()

		# add includes
		self.tu.add_include(c.Comment(' ***Includes*** '))
		self.tu.add_include(c.Include('Python.h', True))
		self.tu.add_include(c.Include('data/c/env.h', False))
		self.tu.add_include(c.Include('data/c/funcobject.h', False))
		self.tu.add_include(c.Include('data/c/genobject.h', False))

		# add common names
		self.builtins = PyObjectLL(None, self)
		self.builtins.declare(self.tu, quals=['static'], name='builtins')
		self.none = PyObjectLL(None, self)
		self.none.declare(self.tu, quals=['static'], name='None')

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
					c.FuncCall(c.ID('__init__'), c.ExprList(c.ID('argc'), c.ID('argv'))),
					c.Assignment('=', c.ID(self.builtins.name), c.FuncCall(c.ID('PyImport_ImportModule'), c.ExprList(c.Constant('string', 'builtins')))),
					c.Assignment('=', c.ID(self.none.name), c.FuncCall(c.ID('PyObject_GetAttrString'), c.ExprList(c.ID(self.builtins.name), c.Constant('string', 'None')))),
			)
		)
		self.tu.add_fwddecl(self.main.decl)
		self.tu.add(c.Comment(' ***Entry Point*** '))
		self.tu.add(self.main)

		# the low-level statment emission context... e.g. the Compound for functions, ifs, etc.
		self.context = self.main.body
		self.context.visitor = self

		# the module we are currently processing
		self.module = None


	def close(self):
		self.main.body.add(c.FuncCall(c.ID('Py_Finalize'), c.ExprList()))
		self.main.body.add(c.Return(c.Constant('integer', 0)))


	@contextmanager
	def global_scope(self, mod, ctx):
		assert self.globals is None
		assert self.scopes == []
		self.globals = mod
		self.scopes = [self.globals]
		self.globals.context = ctx
		yield
		self.scopes = []
		self.globals = None


	@contextmanager
	def new_scope(self, scope, ctx):
		self.scopes.append(scope)
		scope.context = ctx # set the scope's low-level context
		with self.new_label('end'):
			with self.new_context(ctx):
				yield
		self.scopes.pop()


	@contextmanager
	def new_context(self, ctx):
		'''Sets a new context (e.g. C-level {}), without adjusting the python scope or the c scope-context'''
		prior = self.context
		self.context = ctx
		self.context.visitor = self
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
		self.context.visitor = self
		yield
		self.scopes = prior_scopes
		self.context = prior_context


	@contextmanager
	def new_label(self, label_name:str):
		self.flowcontrol.append(label_name)
		yield
		self.flowcontrol.pop()


	@property
	def scope(self):
		return self.scopes[-1]


	def comment(self, cmt):
		'''Optionally add a comment node to the source at the current location.'''
		if self.debug:
			self.context.add(c.Comment(cmt))


	def split_docstring(self, nodes:[py.AST]) -> (Nonable(str), [py.AST]):
		'''Given the body, will pull off the docstring node and return it and the rest of the body.'''
		if nodes and isinstance(nodes[0], py.Expr) and isinstance(nodes[0].value, py.Str):
			if self.opt_elide_docstrings:
				return None, nodes[1:]
			return nodes[0].value.s, nodes[1:]
		return None, nodes


	def create_ll_instance(self, hlnode:HLType):
		inst = self.TYPEMAP[hlnode.get_type().__class__](hlnode, self)
		hlnode.ll = inst
		return inst


	def find_nearest_class_scope(self, err=''):
		for s in reversed(self.scopes):
			if isinstance(s, MelanoClass):
				return s
		raise InvalidScope(err)


	def find_nearest_function_scope(self, err=''):
		for s in reversed(self.scopes):
			if isinstance(s, MelanoFunction):
				return s
		raise InvalidScope(err)


	def find_nearest_method_scope(self, err=''):
		for s in reversed(self.scopes):
			if isinstance(s, MelanoFunction):
				if isinstance(s.owner.parent, MelanoClass):
					return s
		raise InvalidScope(err)


	### Exception Handling ###
	def declare_jump_context(self):
		if not self.scope.context.has_name('__jmp_ctx__'):
			self.scope.context.names.add('__jmp_ctx__')
			self.scope.context.add_variable(c.Decl('__jmp_ctx__', c.PtrDecl(c.TypeDecl('__jmp_ctx__', c.IdentifierType('void'))), init=c.ID('NULL')), False)


	def set_exception(self, ty_inst, inst):
		c_inst = c.ID(inst.name) if inst else c.ID('NULL')
		self.context.add(c.FuncCall(c.ID('PyErr_SetObject'), c.ExprList(c.ID(ty_inst.name), c_inst)))


	def set_exception_str(self, type_name, message):
		if message:
			self.context.add(c.FuncCall(c.ID('PyErr_SetString'), c.ExprList(c.ID(type_name),
																c.Constant('string', PyStringLL.str2c(message)))))
		else:
			self.context.add(c.FuncCall(c.ID('PyErr_SetObject'), c.ExprList(c.ID(type_name), c.ID('NULL'))))



	def clear_exception(self):
		self.context.add(c.FuncCall(c.ID('__err_clear__'), c.ExprList()))


	def capture_error(self):
		filename = self.hl_module.filename
		try: context = self.scope.owner.name
		except IndexError: context = '<module>'
		st = self._current_node.start
		end = self._current_node.end

		if st[0] == end[0]: # one line only
			src = self.hl_module.get_source_line(st[0])
			rng = (st[1], end[1])
		else:
			# if we can't fit the full error context on one line, also print the number of lines longer it goes and the ending column
			src = self.hl_module.get_source_line(st[0]) + ' => (+{},{})'.format(end[0] - st[0], end[1])
			rng = (st[1], len(src))
		src = src.strip().replace('"', '\\"')

		self.context.add(
					c.FuncCall(c.ID('__err_capture__'), c.ExprList(
						c.Constant('string', filename), c.Constant('integer', st[0]), c.ID('__LINE__'), c.Constant('string', context),
						c.Constant('string', src), c.Constant('integer', rng[0]), c.Constant('integer', rng[1]))))


	@contextmanager
	def save_exception(self):
		'''Stores asside the exception with fetch/store for the yielded block'''
		exc_cookie = self.fetch_exception()
		yield exc_cookie
		self.restore_exception(exc_cookie)


	@contextmanager
	def maybe_save_exception(self):
		'''Like save_exception, but checks if an exception is set before saving/restoring.'''
		# if we have an exception set, store it asside during finally processing
		check_err = c.If(c.FuncCall(c.ID('PyErr_Occurred'), c.ExprList()), c.Compound(), None)
		self.context.add(check_err)
		with self.new_context(check_err.iftrue):
			exc_cookie = self.fetch_exception()

		yield exc_cookie

		# if we stored an exception, restore it
		check_restore = c.If(c.ID(exc_cookie[0].name), c.Compound(), None)
		self.context.add(check_restore)
		with self.new_context(check_restore.iftrue):
			self.restore_exception(exc_cookie)


	def maybe_save_exception_normalized_enter(self):
		'''Like maybe_save_exception, but normalizes the cookie and packing it into a tuple before handing 
			it back to the yielded block.'''
		vec = PyTupleLL(None, self)
		vec.declare(self.scope.context)

		# if we have an exception set, store it aside during finally processing
		check_err = self.context.add(c.If(c.FuncCall(c.ID('PyErr_Occurred'), c.ExprList()), c.Compound(), c.Compound()))
		with self.new_context(check_err.iftrue):
			exc_cookie = self.fetch_exception()
			self.normalize_exception_full(exc_cookie)
			vec.new(self.context, 3)
			exc_cookie[0].incref(self.context)
			vec.set_item_unchecked(self.context, 0, exc_cookie[0])
			exc_cookie[1].incref(self.context)
			vec.set_item_unchecked(self.context, 1, exc_cookie[1])
			self.none.incref(self.context)
			vec.set_item_unchecked(self.context, 2, self.none)
		with self.new_context(check_err.iffalse):
			vec.pack(self.context, None, None, None)
		return vec, exc_cookie

	def maybe_restore_exception_normalized_exit(self, exc_cookie):
		# if we stored an exception, restore it
		check_restore = self.context.add(c.If(c.ID(exc_cookie[0].name), c.Compound(), None))
		with self.new_context(check_restore.iftrue):
			self.restore_exception(exc_cookie)


	def fetch_exception(self):
		exc_cookie = (PyObjectLL(None, self), PyObjectLL(None, self), PyObjectLL(None, self))
		self.exc_cookie_stack.append(exc_cookie) #NOTE: this must be matched by a restore
		for part in exc_cookie:
			part.declare(self.scope.context)
		self.context.add(c.FuncCall(c.ID('PyErr_Fetch'), c.ExprList(
																c.UnaryOp('&', c.ID(exc_cookie[0].name)),
																c.UnaryOp('&', c.ID(exc_cookie[1].name)),
																c.UnaryOp('&', c.ID(exc_cookie[2].name)))))
		# NOTE: if we have a real exception here that we are replacing, then restore will decref it, but fetch doesn't incref it for us
		self.context.add(c.FuncCall(c.ID('Py_XINCREF'), c.ExprList(c.ID(exc_cookie[0].name))))
		self.context.add(c.FuncCall(c.ID('Py_XINCREF'), c.ExprList(c.ID(exc_cookie[1].name))))
		self.context.add(c.FuncCall(c.ID('Py_XINCREF'), c.ExprList(c.ID(exc_cookie[2].name))))
		return exc_cookie


	def normalize_exception_full(self, exc_cookie):
		'''Returns the full, normalized exception vector.'''
		self.context.add(c.FuncCall(c.ID('PyErr_NormalizeException'), c.ExprList(
																c.UnaryOp('&', c.ID(exc_cookie[0].name)),
																c.UnaryOp('&', c.ID(exc_cookie[1].name)),
																c.UnaryOp('&', c.ID(exc_cookie[2].name)))))
		self.context.add(c.FuncCall(c.ID('Py_XINCREF'), c.ExprList(c.ID(exc_cookie[0].name))))
		self.context.add(c.FuncCall(c.ID('Py_XINCREF'), c.ExprList(c.ID(exc_cookie[1].name))))
		self.context.add(c.FuncCall(c.ID('Py_XINCREF'), c.ExprList(c.ID(exc_cookie[2].name))))


	def normalize_exception(self, exc_cookie):
		'''Extract and return the real exception value (rather than the type, which is returned by PyErr_Occurred and
			which gets used for matching.'''
		self.normalize_exception_full(exc_cookie)
		exc_cookie[1].incref(self.context)
		return exc_cookie[1]


	def restore_exception(self, exc_cookie:Nonable((PyObjectLL,) * 3)):
		top_cookie = self.exc_cookie_stack.pop()
		assert top_cookie is exc_cookie
		self.context.add(c.FuncCall(c.ID('PyErr_Restore'), c.ExprList(
													c.ID(exc_cookie[0].name), c.ID(exc_cookie[1].name), c.ID(exc_cookie[2].name))))


	def exit_with_exception(self):
		# exceptions need to follow proper flow control....
		self.handle_flowcontrol(
							except_handler=self._except_flowcontrol,
							finally_handler=self._finally_flowcontrol,
							ctxmgr_handler=self._contextmanager_flowcontrol,
							end_handler=self._end_flowcontrol)


	def handle_flowcontrol(self, *, break_handler=None, continue_handler=None,
						except_handler=None, finally_handler=None, ctxmgr_handler=None,
						end_handler=None):
		'''Flow control needs to perform special actions for each flow-control label that the flow-changing operation
			see's under us.  For instance, if we are breaking out of a loop, inside of a try/finally, we need to first
			run the finally, before ending the loop.  This function helps us to visit all possible labels correctly, without
			mistyping or otherwise messing up a relatively complicated loop in each of the several flow-control stmts.
			
			This function accepts per-label processing in kwonly args.  The label processor should emit stmts, as needed
			and return a boolean, False to continue processing labels, and True to finish processing now.
			
			The caller must provide a handler for the 'end' label, as this closes a function and local flow control cannot
			proceed after this point.  
		'''
		labelrules = {
			'break': break_handler,
			'continue': continue_handler,
			'except': except_handler,
			'finally': finally_handler,
			'ctxmgr': ctxmgr_handler,
			'end': end_handler,
		}
		fin = False
		for label in reversed(self.flowcontrol):
			# search labels in the stack for matching handlers
			for labelname, handler in labelrules.items():
				if label.startswith(labelname):
					if handler:
						fin = handler(label)
					else:
						assert label != 'end'
					# quit after we find the first handler, even if our only action is to continue processing
					break
			else:
				raise NotImplementedError("Unknown flowcontrol label statement: {}".format(label))

			# if our latest handler ends processing, continue
			if fin:
				return


	def _end_flowcontrol(self, label):
		self.context.add(c.Goto(label))
		return True


	def _except_flowcontrol(self, label):
		self.context.add(c.Goto(label))
		return True


	def _finally_flowcontrol(self, label):
		ret_label = self.scope.get_label('return_from_finally')
		self.declare_jump_context()
		self.context.add(c.Assignment('=', c.ID('__jmp_ctx__'), c.UnaryOp('&&', c.ID(ret_label))))
		self.context.add(c.Goto(label))
		self.context.add(c.Label(ret_label))
		self.context.add(c.Assignment('=', c.ID('__jmp_ctx__'), c.ID('NULL')))
		return False


	def _contextmanager_flowcontrol(self, label):
		ret_label = self.scope.get_label('return_from_exit')
		self.declare_jump_context()
		self.context.add(c.Assignment('=', c.ID('__jmp_ctx__'), c.UnaryOp('&&', c.ID(ret_label))))
		self.context.add(c.Goto(label))
		self.context.add(c.Label(ret_label))
		self.context.add(c.Assignment('=', c.ID('__jmp_ctx__'), c.ID('NULL')))
		return False


	def _store_any(self, node, src_inst):
		if isinstance(node, py.Attribute):
			o = self.visit(node.value)
			o.set_attr_string(self.context, str(node.attr), src_inst)
		elif isinstance(node, py.Subscript):
			o = self.visit(node.value)
			i = self.visit(node.slice)
			o.set_item(self.context, i, src_inst)
		elif isinstance(node, py.Name):
			tgt = self.visit(node)
			self._store_name(node, src_inst)
		elif isinstance(node, py.Tuple):
			#pdb.set_trace()
			key = PyIntegerLL(None, self)
			key.declare(self.scope.context)
			for i, elt in enumerate(node.elts):
				#pdb.set_trace()
				#if not elt.hl.ll:
				#	_ = self.visit(elt)
				tmp_inst = self.create_ll_instance(elt.hl)
				tmp_inst.declare(self.scope.context)
				key.set_constant(self.context, i)
				src_inst.get_item(self.context, key, elt.hl.ll)
				self._store_any(elt, elt.hl.ll)
		else:
			raise NotImplementedError("Don't know how to assign to type: {}".format(type(node)))


	def _store_name(self, target, val):
		'''
		Common "normal" assignment handler.  Things like for-loop targets and with-stmt vars 
			need the same full suite of potential assignment targets as normal assignments.  With
			the caveat that only assignment will have non-Name children.
		
		target -- the node that is the lhs of the storage.
		'''
		assert isinstance(target, py.Name)

		# NOTE: the hl Name or Ref will always be parented under the right scope
		scope = target.hl.parent
		scope.ll.set_attr_string(self.context, str(target), val)

		# Note: some nodes do not get a visit_Name pass, since we don't have any preceding rhs for the assignment
		#		where we can correctly or easily get the type, 'as' or 'class', etc.  In these cases, we can just retrofit the
		#		value we actually created into the ll target for the hl slot so that future users of the hl instance will be able
		#		to find the correct ll name to use, rather than re-creating it when that users happens to visit_Name on the
		#		node with a missing ll slot.
		if not scope.symbols[str(target)].ll:
			scope.symbols[str(target)].ll = val

		#TODO: this is an optimization; we only want to do it when we can get away with it, and when we can
		#		get away with it, we don't want to assign to the namespace.
		#if tgt:
		#	tgt.assign_name(self.context, val)


	def _load(self, source):
		'''
		source - the underlying name reference that we need to provide access to
		'''
		tmp = PyObjectLL(None, self)
		tmp.declare(self.scope.context)

		# if we have a scope, load from it
		if source.hl.parent.ll:
			source.hl.parent.ll.get_attr_string(self.context, str(source), tmp)
		# otherwise, load from the global scope
		else:
			self.ll_module.get_attr_string(self.context, str(source), tmp)
		return tmp


	def visit_Assert(self, node):
		inst = self.visit(node.test)
		istrue_inst = inst.is_true(self.context)
		check = c.If(c.UnaryOp('!', c.ID(istrue_inst.name)), c.Compound(), None)
		self.context.add(check)
		with self.new_context(check.iftrue):
			s = node.msg.s if node.msg else None
			self.set_exception_str('PyExc_AssertionError', s)
			self.capture_error()
			self.exit_with_exception()


	def visit_Assign(self, node):
		self.comment("Assign: {} = {}".format([str(t) for t in node.targets], str(node.value)))
		val = self.visit(node.value)
		for target in node.targets:
			self._store_any(target, val)


	def visit_Attribute(self, node):
		if node.hl.ll:
			inst = node.hl.ll
		else:
			inst = self.create_ll_instance(node.hl)
			inst.declare(self.scope.context)

		self.comment('Load Attribute "{}.{}"'.format(str(node.value), str(node.attr)))
		if node.ctx == py.Store or node.ctx == py.Aug:
			# load the lhs object into the local c scope
			if isinstance(node.value, py.Name):
				lhs = self._load(node.value)
			else:
				lhs = self.visit(node.value)

			# load the attr off of the lhs, for use as a storage target
			lhs.get_attr_string(self.context, str(node.attr), inst)
			return inst

		elif node.ctx == py.Load:
			# load the attr lhs as normal
			if isinstance(node.value, py.Name):
				lhs = self._load(node.value)
			else:
				lhs = self.visit(node.value)

			# store the attr value into a local tmp variable
			lhs.get_attr_string(self.context, str(node.attr), inst)
			return inst

		else:
			raise NotImplementedError("Unknown Attribute access context: {}".format(node.ctx))


	def visit_AugAssign(self, node):
		self.comment('AugAssign: {} {} {}'.format(str(node.target), self.AUGASSIGN_PRETTY[node.op], str(node.value)))
		val_inst = self.visit(node.value)
		if isinstance(node.target, py.Name):
			tgt_inst = self._load(node.target)
		else:
			tgt_inst = self.visit(node.target)

		# get the intermediate instance
		out_inst = self.create_ll_instance(node.hl)
		out_inst.declare(self.scope.context)

		# perform the op, either returning a copy or getting a new instance
		if node.op == py.BitOr:
			tgt_inst.inplace_bitor(self.context, val_inst, out_inst)
		elif node.op == py.BitXor:
			tgt_inst.inplace_bitxor(self.context, val_inst, out_inst)
		elif node.op == py.BitAnd:
			tgt_inst.inplace_bitand(self.context, val_inst, out_inst)
		elif node.op == py.LShift:
			tgt_inst.inplace_lshift(self.context, val_inst, out_inst)
		elif node.op == py.RShift:
			tgt_inst.inplace_rshift(self.context, val_inst, out_inst)
		elif node.op == py.Add:
			tgt_inst.inplace_add(self.context, val_inst, out_inst)
		elif node.op == py.Sub:
			tgt_inst.inplace_subtract(self.context, val_inst, out_inst)
		elif node.op == py.Mult:
			tgt_inst.inplace_multiply(self.context, val_inst, out_inst)
		elif node.op == py.Div:
			tgt_inst.inplace_divide(self.context, val_inst, out_inst)
		elif node.op == py.FloorDiv:
			tgt_inst.inplace_floor_divide(self.context, val_inst, out_inst)
		elif node.op == py.Mod:
			tgt_inst.inplace_modulus(self.context, val_inst, out_inst)
		elif node.op == py.Pow:
			tgt_inst.inplace_power(self.context, val_inst, out_inst)

		# store back to the owner location
		self._store_any(node.target, out_inst)

		# FIXME: we do need this don't we?
		# decrement the old value
		#tgt_inst.decref(self.context)

		return out_inst


	def visit_BinOp(self, node):
		l = self.visit(node.left)
		r = self.visit(node.right)

		inst = self.create_ll_instance(node.hl)
		inst.declare(self.scope.context)

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


	def visit_BoolOp(self, node):
		self.comment('Binop {}'.format((' ' + self.BOOLOPS_PRETTY[node.op] + ' ').join([str(v) for v in node.values])))

		out = CIntegerLL(None, self, is_a_bool=True)
		out.declare(self.scope.context, init=0)
		# Note: need to re-initialize manually so that use in a loop starts with a default of 0 every time
		self.context.add(c.Assignment('=', c.ID(out.name), c.Constant('integer', 0)))

		# store base context, for restore, since we can't use with stmts here
		base_context = self.context

		# visit each value in order... nest so that we will automatically fall out on failure
		for value in node.values:
			val_inst = self.visit(value)
			val_inst.is_true(self.context, out)

			# Note: our last output is our actual result for both And and Or, since we only get to the last
			#		op if all of our others have been True or False respectively.
			if value is not node.values[-1]:
				# continue to next only if we are False
				if node.op == py.Or:
					ifstmt = self.context.add(c.If(c.UnaryOp('!', c.ID(out.name)), c.Compound(), None))

				# continue to next only if we are True
				elif node.op == py.And:
					ifstmt = self.context.add(c.If(c.ID(out.name), c.Compound(), None))

				# start next comparision in this (failed) context
				self.context = ifstmt.iftrue

		# restore prior context
		self.context = base_context

		return out


	def visit_Bytes(self, node):
		raise NotImplementedError


	def visit_Break(self, node):
		self.comment('break')
		def break_handler(label): # the next break is our ultimate target
			self.context.add(c.FuncCall(c.ID('__err_clear__'), c.ExprList()))
			self.context.add(c.Goto(label))
			return True
		self.handle_flowcontrol(
							break_handler=break_handler,
							finally_handler=self._finally_flowcontrol,
							ctxmgr_handler=self._contextmanager_flowcontrol,
							end_handler=self._end_flowcontrol)



	def visit_Call(self, node):
		def _call_super(self, node, funcinst):
			# get the class type and the instance
			cls = self.find_nearest_class_scope(err='super must be called in a class context: {}'.format(node.start))
			fn = self.find_nearest_method_scope(err='super must be called in a method context: {}'.format(node.start))

			args = PyTupleLL(None, self)
			args.declare(self.scope.context, name='__auto_super_call_args')
			args.pack(self.context, cls.ll.c_obj, fn.ll.get_self_accessor())

			# do the actual call
			rv = PyObjectLL(None, self)
			rv.declare(self.scope.context)
			funcinst.call(self.context, args, None, rv)
			return rv


		def _call_remote(self, node, funcinst):
			# if we are calling super with no args, we need to provide them, since this is the framework's responsibility
			if node.func.hl and node.func.hl.name == 'super' and not node.args:
				return _call_super(self, node, funcinst)

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
			args1 = PyTupleLL(None, self)
			args1.declare(self.scope.context)
			args1.pack(self.context, *args_insts)

			# build the keyword dict
			args2 = None
			kw_insts = []
			if node.keywords:
				for kw in node.keywords:
					valinst = self.visit(kw.value)
					valinst = valinst.as_pyobject(self.context)
					kw_insts.append((str(kw.keyword), valinst))
				if kw_insts:
					args2 = PyDictLL(None, self)
					args2.declare(self.scope.context)
					args2.new(self.context)
					for keyname, valinst in kw_insts:
						args2.set_item_string(self.context, keyname, valinst)

			# begin call output
			self.comment('do call "{}"'.format(str(node.func)))

			# make the call
			rv = PyObjectLL(None, self)
			rv.declare(self.scope.context)
			funcinst.call(self.context, args1, args2, rv)

			# cleanup the args
			args1.delete(self.context)
			if args2: args2.delete(self.context)

			return rv


		#TODO: direct calling, keywords calling, etc
		#TODO: track "type" so we can dispatch to PyCFunction_Call or PyFunction_Call instead of PyObject_Call 
		#TODO: track all call methods (callsite usage types) and see if we can't unpack into a direct c call

		# begin call output
		self.comment('Call function "{}"'.format(str(node.func)))

		# prepare the func name node
		funcinst = self.visit(node.func)

		# TODO: if we are defined locally, we can know the expected calling proc and reorganize our args to it
		#if node.func.hl and node.func.hl.scope:
		#	return _call_local(self, node, funcinst)
		#else:
		#	return _call_remote(self, node, funcinst)
		with self.scope.ll.maybe_recursive_call(self.context):
			rv = _call_remote(self, node, funcinst)

		return rv


	def visit_ClassDef(self, node):
		# declare
		docstring, body = self.split_docstring(node.body)
		inst = self.create_ll_instance(node.hl)
		inst.create_builderfunc(self.tu)
		pyclass_inst = inst.declare_pyclass(self.tu)

		# build the class setup -- this has the side-effect of building all other module-level stuff before
		#	we do the class setup
		with self.new_scope(node.hl, inst.c_builder_func.body):
			# TODO: we should reserve these names in the LL builder
			self.context.reserve_name('self')
			self_inst = PyObjectLL(None, self)
			self_inst.name = 'self'
			self.context.reserve_name('args')
			args_tuple = PyTupleLL(None, self)
			args_tuple.name = 'args'
			self.context.reserve_name('kwargs')
			kwargs_dict = PyDictLL(None, self)
			kwargs_dict.name = 'kwargs'

			# unpack the namespace dict that we will be writing to
			namespace_inst = PyDictLL(None, self)
			namespace_inst.declare(self.scope.context, name='namespace')
			args_tuple.get_unchecked(self.context, 0, namespace_inst)
			namespace_inst.fail_if_null(self.context, namespace_inst.name)
			namespace_inst.incref(self.context)

			inst.set_namespace(namespace_inst)

			inst.intro(self.context, docstring, self.hl_module.owner.name)
			self.visit_nodelist(body)
			inst.outro(self.context)

		# visit any decorators (e.g. calls decorators with args before defining the class)
		deco_fn_insts = []
		if node.decorator_list:
			for deconame in reversed(node.decorator_list):
				decoinst = self.visit(deconame)
				deco_fn_insts.append(decoinst)

		# load the build_class method from builtins
		self.comment("Build class {}".format(str(node.name)))

		# create the name ref string
		c_name_str = PyStringLL(None, self)
		c_name_str.declare(self.scope.context, name=str(node.name) + '_name')
		c_name_str.new(self.context, str(node.name))

		pyfunc = inst.create_builder_funcdef(self.context, self.tu)

		build_class_inst = PyObjectLL(None, self)
		build_class_inst.declare(self.scope.context)
		self.builtins.get_attr_string(self.context, '__build_class__', build_class_inst)

		base_insts = []
		if node.bases:
			for b in node.bases:
				base_insts.append(self.visit(b))

		args = PyTupleLL(None, self)
		args.declare(self.scope.context)
		args.pack(self.context, pyfunc, c_name_str, *base_insts)
		build_class_inst.call(self.context, args, node.kwargs, pyclass_inst)

		# apply decorators to the class
		for decoinst in deco_fn_insts:
			decoargs = PyTupleLL(None, self)
			decoargs.declare(self.scope.context)
			decoargs.pack(self.context, pyclass_inst)
			decoinst.call(self.context, decoargs, None, pyclass_inst)

		# store the name in the scope where we are "created"
		self._store_name(node.name, pyclass_inst)


	def visit_Compare(self, node):
		# format and print the op we are doing for sanity sake
		s = 'Compare ' + str(node.left)
		for o, b in zip(node.ops, node.comparators):
			s += ' {} {}'.format(self.COMPARATORS_PRETTY[o], str(b))
		self.comment(s)

		# initialize new tmp variable with default value of false
		out = CIntegerLL(None, self, is_a_bool=True)
		out.declare(self.scope.context, init=0)

		# Note: we need to initialize the output variable to 0 before the compare since compare can be
		#		used in, for instance, loops, where we need to re-do the comparison correctly every time.
		self.context.add(c.Assignment('=', c.ID(out.name), c.Constant('integer', 0)))

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
			self.context.visitor = self

			# next lhs is current rhs
			a = b

		# we are in our deepest nested context now, where all prior statements have been true
		self.context.add(c.Assignment('=', c.ID(out.name), c.Constant('integer', 1)))

		# reset the context
		self.context = base_context

		return out


	def visit_Continue(self, node):
		self.comment('continue')
		def loop_handler(label):
			self.context.add(c.Goto(label))
			return True
		self.handle_flowcontrol(
							continue_handler=loop_handler,
							finally_handler=self._finally_flowcontrol,
							ctxmgr_handler=self._contextmanager_flowcontrol,
							end_handler=self._end_flowcontrol)


	def visit_Delete(self, node):
		raise NotImplementedError


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


	def visit_Ellipsis(self, node):
		raise NotImplementedError


	def visit_Expr(self, node):
		return self.visit(node.value)


	def visit_ExtSlice(self, node):
		raise NotImplementedError


	def visit_For(self, node):
		#for <target> in <iter>: <body>
		#else: <orelse>

		# the break and continue label
		break_label = self.scope.get_label('break_for')
		continue_label = self.scope.get_label('continue_for')

		# get the PyIter for the iteration object
		iter_obj = self.visit(node.iter)
		iter = PyObjectLL(None, self)
		iter.declare(self.scope.context)
		iter_obj.get_iter(self.context, iter)

		# the gets the object locally inside of the while expr; we do the full assignment inside the body
		tmp = PyObjectLL(None, self)
		tmp.declare(self.scope.context)
		stmt = self.context.add(c.While(c.Assignment('=', c.ID(tmp.name), c.FuncCall(c.ID('PyIter_Next'), c.ExprList(c.ID(iter.name)))), c.Compound()))
		with self.new_context(stmt.stmt):
			with self.new_label(break_label), self.new_label(continue_label):
				self._store_any(node.target, tmp)
				self.visit_nodelist(node.body)
			self.context.add(c.Label(continue_label))

		# handle the no-break case: else
		# if we don't jump to forloop, then we need to just run the else block
		self.visit_nodelist(node.orelse)

		# after else, we get the break target
		self.context.add(c.Label(break_label))


	def visit_FunctionDef(self, node):
		'''
		Notes:
			- Decorators run in the definition scope, not the module scope (unless defined at module scope, obviously)
		'''
		#FIXME: make MelanoCFunction take an attr for __defaults__, __kwdefaults__, and __annotations__

		# for use everywhere else in this function when we need to pass our entire args descriptor down to the implementor
		full_args = (node.args.args or [], node.args.vararg, node.args.kwonlyargs or [], node.args.kwarg)

		# prepare the lowlevel
		docstring, body = self.split_docstring(node.body)
		inst = self.create_ll_instance(node.hl)

		# declare and create non-dependent stuff
		#inst.create_locals(self.tu)
		inst.create_defaults(self.tu, node.args.defaults, node.args.kw_defaults)
		#inst.create_annotations(self.tu)
		inst.create_pystubfunc(self.tu)
		inst.create_runnerfunc(self.tu, *full_args)

		# NOTE: we create all "normal" functions (e.g. methods and non nested funcs) at the module scope (and funcs 
		#		_at_ the module scope) so that class instanciation does not have to re-declare the function object constantly.
		# NOTE: For generator functions, we need to create the function in the containing context so that we have access 
		#		to the parent's coroutine context at runtime.
		# NOTE: For functions that are defined nested, such that they need to keep a closure, we have to create them in 
		#		their runtime context so that we can build and attach the current values of all names so that when they are
		#		called later, they will have access to the correct values (e.g. with recursive use of a returned inner function).
		if not node.hl.is_generator and not node.hl.has_closure:
			with self.module_scope():
				self.comment("Build function {}".format(str(node.name)))
				pycfunc = inst.create_funcdef(self.context, self.tu, docstring)
				# enumerate and attach defaults and keyword defaults
				inst.attach_defaults(self.context,
									[self.visit(default) for default in (node.args.defaults or [])],
							 		[self.visit(kwdefault) for kwdefault in (node.args.kw_defaults or [])])
				# attach annotations to the pycfunction instance
				#inst.attach_annotations(self.context, ...)
		else:
			self.comment("Build function {}".format(str(node.name)))
			pycfunc = inst.create_funcdef(self.context, self.tu, docstring)
			# enumerate and attach defaults and keyword defaults
			inst.attach_defaults(self.context,
								[self.visit(default) for default in (node.args.defaults or [])],
						 		[self.visit(kwdefault) for kwdefault in (node.args.kw_defaults or [])])
			# attach annotations to the pycfunction instance
			#inst.attach_annotations(self.context, ...)

		# visit any decorators (e.g. run decorators with args to get real decorators _before_ defining the function)
		deco_fn_insts = [self.visit(dn) for dn in reversed(node.decorator_list or [])]

		# Build the python stub function
		with self.new_scope(node.hl, inst.c_pystub_func.body):
			self.context.reserve_name('self')
			self_inst = PyObjectLL(None, self)
			self_inst.name = 'self'
			self.context.reserve_name('args')
			args_tuple = PyTupleLL(None, self)
			args_tuple.name = 'args'
			self.context.reserve_name('kwargs')
			kwargs_dict = PyDictLL(None, self)
			kwargs_dict.name = 'kwargs'

			self.comment('Python interface stub function "{}"'.format(str(node.name)))
			inst.stub_intro(self.context)

			# Attach all parameters and names into the local namespace
			# We can't know the convention the caller used, so we need to handle all 
			#  possiblities -- local callers do their own setup and just call the runner.
			inst.stub_load_args(self.context,
										node.args.args or [], node.args.defaults or [],
										node.args.vararg,
										node.args.kwonlyargs or [], node.args.kw_defaults or [],
										node.args.kwarg)

			# call the low-level runner function from the stub
			inst.transfer_to_runnerfunc(self.context, *full_args)

			# emit cleanup and return code
			inst.stub_outro(self.context)

		# build the actual runner function
		with self.new_scope(node.hl, inst.c_runner_func.body):
			inst.runner_intro(self.context)
			inst.runner_load_args(self.context, *full_args)
			inst.runner_load_locals(self.context)
			self.comment('body')
			self.visit_nodelist(node.body)
			inst.runner_outro(self.context)

		# apply any decorators
		if deco_fn_insts:
			self.comment('decorate {}'.format(str(node.name)))
		for decoinst in deco_fn_insts:
			decoargs = PyTupleLL(None, self)
			decoargs.declare(self.scope.context)
			decoargs.pack(self.context, pycfunc)
			decoinst.call(self.context, decoargs, None, pycfunc)

		# store the resulting function into the scope where it's defined
		self.comment('store function name into scope')
		self._store_name(node.name, pycfunc)

		return inst


	def visit_GeneratorExp(self, node):
		raise NotImplementedError


	#def visit_Global(self, node):
	#	not needed


	def visit_If(self, node):
		inst = self.visit(node.test)
		if isinstance(inst, PyObjectLL):
			tmpvar = inst.is_true(self.context)
			test = c.BinaryOp('==', c.Constant('integer', 1), c.ID(tmpvar.name))
		elif isinstance(inst, CIntegerLL):
			test = c.ID(inst.name)
		else:
			raise NotImplementedError('Non-pyobject as value for If test')

		stmt = self.context.add(c.If(test, c.Compound(), c.Compound() if node.orelse else None))
		with self.new_context(stmt.iftrue):
			self.visit_nodelist(node.body)
		if node.orelse:
			with self.new_context(stmt.iffalse):
				self.visit_nodelist(node.orelse)


	def visit_IfExp(self, node):
		raise NotImplementedError


	def visit_Import(self, node):
		def _import_as_name(self, node, name, asname):
			ref = asname.hl.scope
			assert ref is not None
			tgt = self.visit(asname)
			self.comment("Import module {} as {}".format(str(name), str(asname)))
			tmp = PyObjectLL(None, self)
			tmp.declare(self.scope.context)
			if ref.modtype == MelanoModule.PROJECT:
				self.context.add(c.Assignment('=', c.ID(tmp.name), c.FuncCall(c.ID(ref.ll.c_builder_name), c.ExprList())))
			else:
				self.context.add(c.Assignment('=', c.ID(tmp.name), c.FuncCall(c.ID('PyImport_ImportModule'), c.ExprList(
																												c.Constant('string', str(name))))))
			tmp.fail_if_null(self.context, tmp.name)
			tmp.incref(self.context)
			self._store_name(asname, tmp)

		def _import(self, node, name):
			if isinstance(name, py.Name):
				ref = name.hl.scope
				tgt = self.visit(name)
			else:
				assert isinstance(name, py.Attribute)
				ref = name.first().hl.scope
				tgt = self.visit(name.first())

			assert ref is not None

			self.comment("Import module {}".format(str(name)))
			tmp = PyObjectLL(None, self)
			tmp.declare(self.scope.context)
			if ref.modtype == MelanoModule.PROJECT:
				self.context.add(c.Assignment('=', c.ID(tmp.name), c.FuncCall(c.ID(ref.ll.c_builder_name), c.ExprList())))
			else:
				self.context.add(c.Assignment('=', c.ID(tmp.name), c.FuncCall(c.ID('PyImport_ImportModule'), c.ExprList(
																												c.Constant('string', str(name))))))
			tmp.fail_if_null(self.context, tmp.name)
			tmp.incref(self.context)

			#NOTE: if we are importing from an attribute, we also need to import the goal name, so it exists, _and_ we 
			#		need to import the base name so that we can assign it to the target name
			if isinstance(name, py.Attribute):
				basename = str(name.first())
				self.context.add(c.Assignment('=', c.ID(tmp.name), c.FuncCall(c.ID('PyImport_ImportModule'), c.ExprList(
																													c.Constant('string', str(basename))))))
				tmp.fail_if_null(self.context, tmp.name)
				self._store_name(name.first(), tmp)
			else:
				self._store_name(name, tmp)

		for alias in node.names:
			if alias.asname:
				_import_as_name(self, node, alias.name, alias.asname)
			else:
				_import(self, node, alias.name)


	def visit_ImportFrom(self, node):
		mod = node.module.hl

		# load the module reference
		tmp = PyObjectLL(None, self)
		tmp.declare(self.scope.context)
		if mod.modtype == MelanoModule.PROJECT:
			# call the builder function to construct or access the module
			self.context.add(c.Assignment('=', c.ID(tmp.name), c.FuncCall(c.ID(mod.ll.c_builder_name), c.ExprList())))
		else:
			# import the module at the c level
			modname = '.' * node.level + str(node.module)
			self.context.add(c.Assignment('=', c.ID(tmp.name), c.FuncCall(c.ID('PyImport_ImportModule'), c.ExprList(
																												c.Constant('string', str(modname))))))
		tmp.fail_if_null(self.context, tmp.name)
		tmp.incref(self.context)

		# pluck names out of the module and into our namespace
		def _import_name(name, asname):
			# load the name off of the module
			val = PyObjectLL(None, self)
			val.declare(self.scope.context)
			self.context.add(c.Assignment('=', c.ID(val.name), c.FuncCall(c.ID('PyObject_GetAttrString'), c.ExprList(
																		c.ID(tmp.name), c.Constant('string', PyStringLL.str2c(str(name)))))))
			val.fail_if_null(self.context, val.name)
			if asname:
				self._store_name(asname, val)
			else:
				self._store_name(name, val)

		for alias in node.names:
			if alias.asname:
				tgt = self.visit(alias.asname)
				_import_name(alias.name, alias.asname)
			else:
				if str(alias.name) == '*':
					for name in mod.lookup_star():
						py_name = py.Name(name, py.Store, None)
						py_name.hl = self.hl_module.symbols[name]
						_import_name(py_name, None)
				else:
					tgt = self.visit(alias.name)
					_import_name(alias.name, alias.asname)


	def visit_Index(self, node):
		#NOTE: Pass through index values... not sure why python ast wraps these rather than just having a value.
		node.hl = node.value.hl
		node.hl.ll = self.visit(node.value)
		return node.hl.ll


	def visit_Lambda(self, node):
		raise NotImplementedError


	#def visit_List(self, node):
	#	See visit_Tuple for actual implementation


	def preallocate(self, node):
		'''Called once for every module before we enter the emit phase.  We use this to acquire a ll builder name
			for every module so that we can do things like triangular imports without running into problems.'''
		node.hl.ll = self.create_ll_instance(node.hl)


	def visit_Module(self, node):
		# we need the toplevel available to all children so that we can do lookups for globals
		self.hl_module = node.hl
		self.ll_module = self.hl_module.ll

		# setup the module
		self.ll_module.declare(self.tu)

		# set the initial context
		with self.new_context(self.ll_module.c_builder_func.body):
			with self.new_label('end'):
				# setup the module
				self.ll_module.return_existing(self.context)
				self.comment('Create module "{}" as "{}"'.format(self.hl_module.name, self.hl_module.owner.name))
				self.ll_module.new(self.context)
				self.ll_module.get_dict(self.context)

				self.ll_module.intro(self.context)

				# visit all children
				with self.global_scope(self.hl_module, self.context):
					# load and attach special attributes to the module dict
					self.ll_module.set_initial_string_attribute(self.context, '__name__', self.hl_module.owner.name)
					self.ll_module.set_initial_string_attribute(self.context, '__file__', self.hl_module.filename)
					docstring, body = self.split_docstring(node.body)
					self.ll_module.set_initial_string_attribute(self.context, '__doc__', docstring)

					# record the top-level context in the scope, so we can declare toplevel variables when in a sub-contexts
					self.scope.context = self.context

					# visit all children
					self.visit_nodelist(body)

			# cleanup and return
			self.ll_module.outro(self.context)

		# the only module we want to load automatically at runtime is the main module
		if self.hl_module.owner.name == '__main__':
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
		if node.ctx in [py.Store, py.Param, py.Aug]:
			if not node.hl.ll:
				inst = self.create_ll_instance(node.hl)
				inst.declare(self.scope.context)
			return node.hl.ll

		# if we are loading a name, we have to search for the name's location
		elif node.ctx == py.Load:
			return self._load(node)

		else:
			raise NotImplementedError("unknown context for name: {}".format(node.ctx))


	#def visit_NonLocal(self, node):
	#	raise NotImplementedError


	def visit_Num(self, node):
		inst = self.create_ll_instance(node.hl)
		inst.declare(self.scope.context)
		inst.new(self.context, node.n)
		return inst


	def visit_Pass(self, node):
		self.comment('pass')


	def visit_Raise(self, node):
		self.comment('raise')

		if not node.exc:
			exc_cookie = self.exc_cookie_stack[-1]
			self.restore_exception(exc_cookie)
			self.exc_cookie_stack.append(exc_cookie)
			self.handle_flowcontrol(
								except_handler=self._except_flowcontrol,
								finally_handler=self._finally_flowcontrol,
								ctxmgr_handler=self._contextmanager_flowcontrol,
								end_handler=self._end_flowcontrol)
			return

		#FIXME: re-raise existing context if node.exc is not present
		inst = self.visit(node.exc)

		#TODO: we can probably figure out if the object is a type if we have static_builtins or such
		'''
		if(PyObject_IsInstance(inst.name, PyType_Type)) {
			PyErr_SetObject(inst.name, ??);
		} else {
			PyErr_SetObject(PyObject_Type(inst.name), inst.name);
		}
		goto end;
		'''
		is_a_type = inst.is_instance(self.context, PyTypeLL)
		if_stmt = c.If(c.ID(is_a_type.name), c.Compound(), c.Compound())
		self.context.add(if_stmt)
		with self.new_context(if_stmt.iftrue):
			self.set_exception(inst, None)
		with self.new_context(if_stmt.iffalse):
			ty_inst = PyTypeLL(None, self)
			ty_inst.declare(self.scope.context)
			inst.get_type(self.context, ty_inst)
			self.set_exception(ty_inst, inst)
		self.capture_error()
		self.exit_with_exception()

		# do exception flow-control
		self.handle_flowcontrol(
							except_handler=self._except_flowcontrol,
							finally_handler=self._finally_flowcontrol,
							ctxmgr_handler=self._contextmanager_flowcontrol,
							end_handler=self._end_flowcontrol)


	def visit_Return(self, node):
		# get the return value for when we exit
		if node.value:
			inst = self.visit(node.value)
			self.context.add(c.Assignment('=', c.ID('__return_value__'), c.ID(inst.name)))
		else:
			self.context.add(c.Assignment('=', c.ID('__return_value__'), c.ID(self.none.name)))
		self.context.add(c.FuncCall(c.ID('Py_INCREF'), c.ExprList(c.ID('__return_value__'))))

		# do exit flowcontrol to handle finally blocks
		self.handle_flowcontrol(
							finally_handler=self._finally_flowcontrol,
							ctxmgr_handler=self._contextmanager_flowcontrol,
							end_handler=self._end_flowcontrol)


	def visit_Set(self, node):
		inst = self.create_ll_instance(node.hl)
		inst.declare(self.scope.context)
		inst.new(self.context, None)
		for v in node.elts:
			vinst = self.visit(v)
			inst.add(self.context, vinst)
		return inst


	def visit_Slice(self, node):
		raise NotImplementedError


	def visit_Starred(self, node):
		raise NotImplementedError


	def visit_Str(self, node):
		inst = self.create_ll_instance(node.hl)
		inst.declare(self.scope.context)
		inst.new(self.context, PyStringLL.str2c(node.s))
		return inst


	def visit_Subscript(self, node):
		if node.ctx == py.Store:
			raise NotImplementedError("Subscript store needs special casing at assignment site")
		elif node.ctx in [py.Load, py.Aug]:
			kinst = self.visit(node.slice)
			tgtinst = self.visit(node.value)
			tmp = PyObjectLL(None, self)
			tmp.declare(self.scope.context)
			tgtinst.get_item(self.context, kinst, tmp)
			return tmp
		else:
			raise NotImplementedError("Unknown Attribute access context: {}".format(node.ctx))


	def visit_TryExcept(self, node):
		self.comment('try-except')
		tryend_label = self.scope.get_label('tryend')
		tryelseend_label = self.scope.get_label('tryelseend')

		# add this exception to the flow control context in the try body
		except_label = self.scope.get_label('except')
		with self.new_label(except_label):
			self.visit_nodelist(node.body)

		# if we get to the end of the try block without failing, jump past the except block 
		self.context.add(c.Goto(tryend_label))

		# branch target for jumping to this exception
		self.context.add(c.Label(except_label))

		### exception dispatch logic
		## Check if there was actually an exception -- raise if not
		exc_type_inst = PyObjectLL(None, self)
		exc_type_inst.declare(self.scope.context)
		self.context.add(c.Assignment('=', c.ID(exc_type_inst.name), c.FuncCall(c.ID('PyErr_Occurred'), c.ExprList())))
		exc_type_inst.fail_if_null(self.context, exc_type_inst.name)
		## Store the exception during exception processing
		with self.save_exception() as exc_cookie:
			## check the exception handles against the exception that occurred
			parts = [] # [c.If]
			for handler in node.handlers:
				# check if this is the exception that matches
				if handler.type:
					class_inst = self.visit(handler.type)
					test = c.If(c.FuncCall(c.ID('PyErr_GivenExceptionMatches'), c.ExprList(c.ID(exc_type_inst.name), c.ID(class_inst.name))), c.Compound(), None)
				# if no handler type, this is the catchall
				# Note: we use an ifelse for this, since else is our no-match case
				else:
					test = c.If(c.Constant('integer', 1), c.Compound(), None)
				# implement the body of the matching handler
				with self.new_context(test.iftrue):
					# if we named the exception, fetch (or build it) from the cookie
					if handler.name:
						exc_val_inst = self.normalize_exception(exc_cookie)
						self._store_name(handler.name, exc_val_inst)
					self.visit_nodelist(handler.body)
				# append next if/handler
				parts.append(test)

			## chain together all if's into a big if-elif structure
			# Note: leave last if as 'current' so we can attach an else to it's iffalse
			current = parts[0]
			for p in parts[1:]:
				current.iffalse = p
				current = p

			## the final else triggers if we didn't match an exception
			current.iffalse = c.Compound()
			with self.new_context(current.iffalse):
				# if we have an else clause, implement it directly as an else here
				if node.orelse:
					self.visit_nodelist(node.orelse)

				# otherwise, if we reach the else clause of the match, nobody handled the error; raise it to the next frame
				else:
					#NOTE: if we get here we will be leaving, so we need to restore the exception before visiting this
					top_cookie = self.exc_cookie_stack[-1]
					self.restore_exception(top_cookie)
					self.exc_cookie_stack.append(top_cookie) # re-save so we can pop again at exit
					self.handle_flowcontrol(
										finally_handler=self._finally_flowcontrol,
										ctxmgr_handler=self._contextmanager_flowcontrol,
										end_handler=self._end_flowcontrol)

			## add the if-chain to the body
			self.context.add(parts[0])

		# if we fall off the end of the exception handler, we are considered cleared
		self.clear_exception()
		self.context.add(c.Goto(tryelseend_label))

		# if we finish, successfully, jump here to skip the exeption handling and run the else block
		self.context.add(c.Label(tryend_label))
		self.visit_nodelist(node.orelse)

		# if we reach the end of the except block, don't run the else block
		self.context.add(c.Label(tryelseend_label))


	def visit_TryFinally(self, node):
		self.comment('try-finally')

		# add this finally to the flow control context in the try body
		label = self.scope.get_label('finally')
		with self.new_label(label):
			self.visit_nodelist(node.body)

		# branch target for jumping to a finally clause
		self.context.add(c.Label(label))

		# handle the final stmt
		with self.maybe_save_exception():
			self.visit_nodelist(node.finalbody)

		# if the top-level needs control back to complete, it will set __jmp_ctx__
		self.context.add(c.If(c.ID('__jmp_ctx__'), c.Compound(c.Goto(c.UnaryOp('*', c.ID('__jmp_ctx__')))), None))


	def visit_Tuple(self, node):
		if node.ctx in [py.Load, py.Aug]:
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
		else:
			raise NotImplementedError


	visit_List = visit_Tuple


	def visit_While(self, node):
		# get a break and continue label
		break_label = self.scope.get_label('break_while')
		continue_label = self.scope.get_label('continue_while')

		# Note: we use a do{}while(1) with manual break, instead of the more direct while(){}, so that we only
		#		have to visit/emit the test code once, rather than once outside and once at the end of the loop.
		dowhile = c.DoWhile(c.Constant('integer', 1), c.Compound())
		self.context.add(dowhile)
		with self.new_context(dowhile.stmt):
			with self.new_label(break_label), self.new_label(continue_label):
				# perform the test
				test_inst = self.visit(node.test)
				#TODO: short circuit this somehow... make is_true for CIntegerLL perhaps?
				#			also fix in visit_If if we do work it out
				if isinstance(test_inst, PyObjectLL):
					tmpvar = test_inst.is_true(self.context)
					test = c.BinaryOp('==', c.Constant('integer', 0), c.ID(tmpvar))
				elif isinstance(test_inst, CIntegerLL):
					test = c.UnaryOp('!', c.ID(test_inst.name))
				else:
					raise NotImplementedError('Non-pyobject as value for If test')

				# exit if our test failed
				self.context.add(c.If(test, c.Compound(c.Break()), None))

				# do loop actions
				self.visit_nodelist(node.body)

			# continue on to immediately before test for continue
			self.context.add(c.Label(continue_label))

		# add the non-break (at the python level, not the c level) case for else
		self.visit_nodelist(node.orelse)
		self.context.add(c.Label(break_label))


	def visit_With(self, node):
		ctx = self.visit(node.context_expr)

		# load enter and exit
		enter_fn_inst = PyObjectLL(None, self)
		enter_fn_inst.declare(self.scope.context)
		ctx.get_attr_string(self.context, '__enter__', enter_fn_inst)
		exit_fn_inst = PyObjectLL(None, self)
		exit_fn_inst.declare(self.scope.context)
		ctx.get_attr_string(self.context, '__exit__', exit_fn_inst)

		tmp = PyObjectLL(None, self)
		tmp.declare(self.scope.context)

		# call enter
		args = PyTupleLL(None, self)
		args.declare(self.scope.context)
		args.pack(self.context)
		enter_fn_inst.call(self.context, args, None, tmp)

		# if we provide the result in the namespace, set it
		if node.optional_vars:
			var = self.visit(node.optional_vars)
			self._store_name(node.optional_vars, tmp)

		# create a label we can jump to at with-stmt end if control flow tries to take us away
		#		we just use a finally here, rather than taking a custom approach, because that is
		#		the exact semantics we want to provide.
		exit_label = self.scope.get_label('ctxmgr')

		# visit the body, keeping a record of the finally context we need to use when exiting
		with self.new_label(exit_label):
			if isinstance(node.body, list):
				self.visit_nodelist(node.body)
			else:
				self.visit(node.body)

		# mark exit as a finally target
		self.context.add(c.Label(exit_label))

		# query for a possibly set exception
		argvec, exc_cookie = self.maybe_save_exception_normalized_enter()

		# do the __exit__ call
		out_var = PyObjectLL(None, self)
		out_var.declare(self.scope.context)
		exit_fn_inst.call(self.context, argvec, None, out_var)
		argvec.delete(self.context)

		# raise the exception if the output is False, otherwise supress
		suppress_inst = out_var.is_true(self.context)
		restore_if = self.context.add(c.If(c.UnaryOp('!', c.ID(suppress_inst.name)), c.Compound(), c.Compound()))
		with self.new_context(restore_if.iftrue):
			self.maybe_restore_exception_normalized_exit(exc_cookie)
		with self.new_context(restore_if.iffalse):
			self.context.add(c.FuncCall(c.ID('__err_clear__'), c.ExprList()))

			# NOTE: just clearing an error isn't enough here: our flowcontrol handler will assume an exception will raise out
			#		of this context, so we need to also stop ourself from jumping out of this context.  Since the error is squashed
			#		we can just continue on our way.
			self.context.add(c.Assignment('=', c.ID('__jmp_ctx__'), c.ID('NULL')))

		# if the top-level needs control back to complete, it will set __jmp_ctx__
		self.declare_jump_context()
		self.context.add(c.If(c.ID('__jmp_ctx__'), c.Compound(c.Goto(c.UnaryOp('*', c.ID('__jmp_ctx__')))), None))


	def visit_UnaryOp(self, node):
		o = self.visit(node.operand)

		inst = PyObjectLL(None, self)
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


	def visit_Yield(self, node):
		# get the returned instance
		rv_inst = self.visit(node.value)
		self.scope.ll.do_yield(self.context, rv_inst)



	### Comprehensions ###
	def visit_comp_generators(self, generators, setter):
		node = generators[0]

		iter_obj = self.visit(node.iter)

		# get the PyIter for the iteration object
		iter = PyObjectLL(None, self)
		iter.declare(self.scope.context)
		iter_obj.get_iter(self.context, iter)

		# the gets the object locally inside of the while expr; we do the full assignment inside the body
		tmp = PyObjectLL(None, self)
		tmp.declare(self.scope.context)
		stmt = self.context.add(c.While(c.Assignment('=', c.ID(tmp.name), c.FuncCall(c.ID('PyIter_Next'), c.ExprList(c.ID(iter.name)))), c.Compound()))
		with self.new_context(stmt.stmt):
			# set this loops variable
			self._store_any(node.target, tmp)

			# if we have selectors on this generator, visit them recursively
			if node.ifs:
				return self.visit_comp_ifs(generators, 0, setter)

			# if we have more generators, visit them, otherwise set our targets
			if len(generators) > 1:
				return self.visit_comp_generators(generators[1:], setter)

			# if out of generators, go to setting our result
			setter()


	def visit_comp_ifs(self, generators, offset, setter):
		node = generators[0].ifs[offset]
		offset += 1

		# get our truth value for the test
		inst = self.visit(node)
		if isinstance(inst, PyObjectLL):
			tmpvar = inst.is_true(self.context)
			test = c.BinaryOp('==', c.Constant('integer', 1), c.ID(tmpvar.name))
		elif isinstance(inst, CIntegerLL):
			test = c.ID(inst.name)
		else:
			raise NotImplementedError('Non-pyobject as value for If test')

		# create the if stmt
		stmt = self.context.add(c.If(test, c.Compound(), None))
		with self.new_context(stmt.iftrue):
			# if we have more ifs to visit, then go there
			if offset < len(generators[0].ifs):
				return self.visit_comp_ifs(generators, offset, setter)

			# if we are out of ifs, visit the remaining generators
			if len(generators) > 1:
				return self.visit_comp_generators(generators[1:], setter)

			# if out of generators, go to setting our result
			setter()


	def visit_DictComp(self, node):
		dict_inst = self.create_ll_instance(node.hl)
		dict_inst.prepare_locals(self.scope.context)

		out = PyDictLL(None, self)
		out.declare(self.context, name="_dictcomp_")
		out.new(self.context)

		def _set():
			k_inst = self.visit(node.key)
			v_inst = self.visit(node.value)
			out.set_item(self.context, k_inst, v_inst)
		self.visit_comp_generators(node.generators, _set)

		return out


	def visit_ListComp(self, node):
		list_inst = self.create_ll_instance(node.hl)
		list_inst.prepare_locals(self.scope.context)

		out = PyListLL(None, self)
		out.declare(self.context, name="_listcomp_")
		out.new(self.context)

		def _set():
			obj = self.visit(node.elt)
			out.append(self.context, obj)
		self.visit_comp_generators(node.generators, _set)

		return out


	def visit_SetComp(self, node):
		set_inst = self.create_ll_instance(node.hl)
		set_inst.prepare_locals(self.scope.context)

		out = PySetLL(None, self)
		out.declare(self.context, name="_setcomp_")
		out.new(self.context)

		def _set():
			obj = self.visit(node.elt)
			out.add(self.context, obj)
		self.visit_comp_generators(node.generators, _set)

		return out


