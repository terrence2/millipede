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
from melano.hl.nameref import NameRef
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
		static_builtins			Assume that builtin names are not modified outside
		static_defaults		Assume that function __defaults__ and __kwdefaults__ are not modified outside 
	
	Meta Options:
	(Meta options turn on several underlying options all at once in a package.)
		no_external_code	Sets all options that disable optimizations based on possible actions of not-present code.
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


	def __init__(self, opt_level, opt_options, hl_builtins):
		super().__init__()

		# Emit helpful source-level comments
		self.debug = True

		# options
		self.opt_level = opt_level
		self.opt_options = opt_options
		self.opt_elide_docstrings = 'nodocstrings' in opt_options

		# the python hl walker context
		self.scopes = []

		# There are a number of constructs that change the flow of control in python in ways that are not directly
		# 		representable in c without goto.  We use the flow-control list to allow constructs that change the flow of
		#		control to work together to create a correct goto-web.
		self.flowcontrol = []

		# A stack that contains the current nest of loop variable names.
		self.loop_vars = []

		# This contains the set of all available (at a C scope) temp var names and the set of all in-use (in an expr) names.
		self.tmp_names = [set()]
		self.tmp_used = [set()]

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
		self.tu.add_include(c.Include('env.h', False))
		self.tu.add_include(c.Include('closure.h', False))
		self.tu.add_include(c.Include('funcobject.h', False))
		self.tu.add_include(c.Include('genobject.h', False))

		# add common names
		self.hl_builtins = hl_builtins
		self.builtins = PyObjectLL(hl_builtins, self)
		self.builtins.declare(is_global=True, quals=['static'])
		self.builtin_refs = {}
		for name in PY_BUILTINS:
			self.builtin_refs[name] = PyObjectLL(self.hl_builtins.lookup(name), self)
			self.builtin_refs[name].declare(is_global=True, quals=['static'])
		self.none = self.builtin_refs['None']

		# the main function -- handles init, cleanup, and error printing at top level
		self.tu.reserve_global_name('main')
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
			)
		)
		for name in PY_BUILTINS:
			self.main.body.add(c.Assignment('=', c.ID(self.builtin_refs[name].name), c.FuncCall(c.ID('PyObject_GetAttrString'), c.ExprList(c.ID(self.builtins.name), c.Constant('string', name)))))

		self.tu.add_fwddecl(self.main.decl)
		self.tu.add(c.Comment(' ***Entry Point*** '))
		self.tu.add(self.main)

		# the low-level statment emission context... e.g. the Compound for functions, ifs, etc.
		self.ctx = self.main.body

		# the module we are currently processing
		self.module = None


	def close(self):
		self.main.body.add(c.FuncCall(c.ID('Py_Finalize'), c.ExprList()))
		self.main.body.add(c.Return(c.Constant('integer', 0)))


	@contextmanager
	def main_scope(self):
		class _FakeScope: pass
		assert self.scopes == []
		self.scopes = [_FakeScope()]
		self.scope.ctx = self.main.body
		yield
		self.scopes = []


	@contextmanager
	def module_scope(self, mod, ctx):
		assert self.scopes == []
		self.scopes = [mod]
		self.scope.ctx = ctx
		yield
		self.scopes = []


	@contextmanager
	def new_scope(self, scope, ctx):
		self.scopes.append(scope)
		scope.ctx = ctx # set the scope's low-level context
		with self.new_label('end'):
			with self.new_context(ctx):
				yield
		self.scopes.pop()


	@contextmanager
	def new_context(self, ctx):
		'''Sets a new context (e.g. C-level {}), without adjusting the python scope or the c scope-context'''
		prior = self.ctx
		self.ctx = ctx
		yield
		self.ctx = prior


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
			self.ctx.add(c.Comment(cmt))


	def on_line_changed(self, lineno):
		self.ctx.add(c.WhiteSpace(''))


	def split_docstring(self, nodes:[py.AST]) -> (Nonable(str), [py.AST]):
		'''Given the body, will pull off the docstring node and return it and the rest of the body.'''
		if nodes and isinstance(nodes[0], py.Expr) and isinstance(nodes[0].value, py.Str):
			if self.opt_elide_docstrings:
				return None, nodes[1:]
			return PyStringType.dequote(nodes[0].value.s), nodes[1:]
		return None, nodes


	def create_ll_instance(self, hlnode:HLType):
		if hlnode.ll:
			return hlnode.ll
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
		if not self.scope.ctx.has_name('__jmp_ctx__'):
			self.scope.ctx.names.add('__jmp_ctx__')
			self.scope.ctx.add_variable(c.Decl('__jmp_ctx__', c.PtrDecl(c.TypeDecl('__jmp_ctx__', c.IdentifierType('void'))), init=c.ID('NULL')), False)


	def set_exception(self, ty_inst, inst):
		c_inst = c.ID(inst.name) if inst else c.ID('NULL')
		self.ctx.add(c.FuncCall(c.ID('PyErr_SetObject'), c.ExprList(c.ID(ty_inst.name), c_inst)))


	def set_exception_str(self, type_name, message):
		if isinstance(message, str):
			self.ctx.add(c.FuncCall(c.ID('PyErr_SetString'), c.ExprList(c.ID(type_name),
																c.Constant('string', PyStringLL.escape_c_string(message)))))
		elif isinstance(message, PyObjectLL):
			self.ctx.add(c.FuncCall(c.ID('PyErr_SetObject'), c.ExprList(c.ID(type_name), c.ID(message.name))))
		else:
			self.ctx.add(c.FuncCall(c.ID('PyErr_SetObject'), c.ExprList(c.ID(type_name), c.ID('NULL'))))


	def set_exception_format(self, type_name, message, *insts):
		assert isinstance(message, str)
		ids = [c.ID(inst.name) for inst in insts]
		self.ctx.add(c.FuncCall(c.ID('PyErr_Format'), c.ExprList(c.ID(type_name), c.Constant('string', message), *ids)))


	def clear_exception(self):
		self.ctx.add(c.FuncCall(c.ID('__err_clear__'), c.ExprList()))


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

		self.ctx.add(
					c.FuncCall(c.ID('__err_capture__'), c.ExprList(
						c.Constant('string', PyStringLL.escape_c_string(filename)),
						c.Constant('integer', st[0]), c.ID('__LINE__'),
						c.Constant('string', PyStringLL.escape_c_string(context)),
						c.Constant('string', PyStringLL.escape_c_string(src)),
						c.Constant('integer', rng[0]),
						c.Constant('integer', rng[1]))))


	@contextmanager
	def save_exception(self):
		'''Stores aside the exception with fetch/store for the yielded block'''
		exc_cookie = self.fetch_exception()
		yield exc_cookie
		self.restore_exception(exc_cookie)


	@contextmanager
	def maybe_save_exception(self):
		'''Like save_exception, but checks if an exception is set before saving/restoring.'''
		# if we have an exception set, store it asside during finally processing
		check_err = self.ctx.add(c.If(c.FuncCall(c.ID('PyErr_Occurred'), c.ExprList()), c.Compound(), None))
		with self.new_context(check_err.iftrue):
			exc_cookie = self.fetch_exception()

		yield exc_cookie

		# if we stored an exception, restore it
		check_restore = c.If(c.ID(exc_cookie[0].name), c.Compound(), None)
		self.ctx.add(check_restore)
		with self.new_context(check_restore.iftrue):
			self.restore_exception(exc_cookie)


	def maybe_save_exception_normalized_enter(self):
		'''Like maybe_save_exception, but normalizes the cookie and packing it into a tuple before handing 
			it back to the yielded block.'''
		vec = PyTupleLL(None, self)
		vec.declare()

		# if we have an exception set, store it aside during finally processing
		check_err = self.ctx.add(c.If(c.FuncCall(c.ID('PyErr_Occurred'), c.ExprList()), c.Compound(), c.Compound()))
		with self.new_context(check_err.iftrue):
			exc_cookie = self.fetch_exception()
			self.normalize_exception_full(exc_cookie)
			vec.new(3)
			exc_cookie[0].incref()
			vec.set_item_unchecked(0, exc_cookie[0])
			exc_cookie[1].incref()
			vec.set_item_unchecked(1, exc_cookie[1])
			self.none.incref()
			vec.set_item_unchecked(2, self.none)
		with self.new_context(check_err.iffalse):
			vec.pack(None, None, None)
		return vec, exc_cookie

	def maybe_restore_exception_normalized_exit(self, exc_cookie):
		# if we stored an exception, restore it
		check_restore = self.ctx.add(c.If(c.ID(exc_cookie[0].name), c.Compound(), None))
		with self.new_context(check_restore.iftrue):
			self.restore_exception(exc_cookie)


	def fetch_exception(self):
		exc_cookie = (PyObjectLL(None, self), PyObjectLL(None, self), PyObjectLL(None, self))
		self.exc_cookie_stack.append(exc_cookie) #NOTE: this must be matched by a restore
		for part in exc_cookie:
			part.declare()
		self.ctx.add(c.FuncCall(c.ID('PyErr_Fetch'), c.ExprList(
																c.UnaryOp('&', c.ID(exc_cookie[0].name)),
																c.UnaryOp('&', c.ID(exc_cookie[1].name)),
																c.UnaryOp('&', c.ID(exc_cookie[2].name)))))
		# NOTE: if we have a real exception here that we are replacing, then restore will decref it, but fetch doesn't incref it for us
		self.ctx.add(c.FuncCall(c.ID('Py_XINCREF'), c.ExprList(c.ID(exc_cookie[0].name))))
		self.ctx.add(c.FuncCall(c.ID('Py_XINCREF'), c.ExprList(c.ID(exc_cookie[1].name))))
		self.ctx.add(c.FuncCall(c.ID('Py_XINCREF'), c.ExprList(c.ID(exc_cookie[2].name))))
		return exc_cookie


	def normalize_exception_full(self, exc_cookie):
		'''Returns the full, normalized exception vector.'''
		self.ctx.add(c.FuncCall(c.ID('PyErr_NormalizeException'), c.ExprList(
																c.UnaryOp('&', c.ID(exc_cookie[0].name)),
																c.UnaryOp('&', c.ID(exc_cookie[1].name)),
																c.UnaryOp('&', c.ID(exc_cookie[2].name)))))
		exc_cookie[0].xincref()
		exc_cookie[1].xincref()
		exc_cookie[2].xincref()


	def normalize_exception(self, exc_cookie):
		'''Extract and return the real exception value (rather than the type, which is returned by PyErr_Occurred and
			which gets used for matching.'''
		self.normalize_exception_full(exc_cookie)
		#TODO: is this incref correct... normalize_exception_full already does one xincref
		exc_cookie[1].incref()
		return exc_cookie[1]


	def restore_exception(self, exc_cookie:Nonable((PyObjectLL,) * 3)):
		top_cookie = self.exc_cookie_stack.pop()
		assert top_cookie is exc_cookie
		self.ctx.add(c.FuncCall(c.ID('PyErr_Restore'), c.ExprList(
													c.ID(exc_cookie[0].name), c.ID(exc_cookie[1].name), c.ID(exc_cookie[2].name))))


	def exit_with_exception(self):
		# exceptions need to follow proper flow control....
		self.handle_flowcontrol(except_handler=self._except_flowcontrol)


	def handle_flowcontrol(self, *, break_handler=None, continue_handler=None,
						except_handler=None, finally_handler=None, ctxmgr_handler=None,
						end_handler=None):
		'''Emits code that performs flow operations, e.g. from a loop or function exit, or when an exception
			occurs.
		
			Flow control needs to perform special actions for each flow-control label that the flow-changing operation
			see's under us.  For instance, if we are breaking out of a loop, inside of a try/finally, we need to first
			run the finally, before ending the loop.  This function helps us to visit all possible labels correctly, without
			mistyping or otherwise messing up a relatively complicated loop in each of the several flow-control stmts.
			
			This function accepts per-label processing in kwonly args.  The label processor should emit stmts, as needed
			and return a boolean, False to continue processing labels, and True to finish processing now.  This allows some
			flow control points to behave differently from others, e.g. we only want to go to break labels if our flow-control
			operation is a break statement. 
			
			Some of the handlers are required, as they are always obeyed, as per the language specs.  These are:
				finally, ctxmgr, and end
		'''
		if not finally_handler: finally_handler = self._finally_flowcontrol
		if not ctxmgr_handler: ctxmgr_handler = self._contextmanager_flowcontrol
		if not end_handler: end_handler = self._end_flowcontrol
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
		self.ctx.add(c.Goto(label))
		return True


	def _except_flowcontrol(self, label):
		self.ctx.add(c.Goto(label))
		return True


	def _finally_flowcontrol(self, label):
		ret_label = self.scope.get_label('return_from_finally')
		self.declare_jump_context()
		self.ctx.add(c.Assignment('=', c.ID('__jmp_ctx__'), c.UnaryOp('&&', c.ID(ret_label))))
		self.ctx.add(c.Goto(label))
		self.ctx.add(c.Label(ret_label))
		self.ctx.add(c.Assignment('=', c.ID('__jmp_ctx__'), c.ID('NULL')))
		return False


	def _contextmanager_flowcontrol(self, label):
		ret_label = self.scope.get_label('return_from_exit')
		self.declare_jump_context()
		self.ctx.add(c.Assignment('=', c.ID('__jmp_ctx__'), c.UnaryOp('&&', c.ID(ret_label))))
		self.ctx.add(c.Goto(label))
		self.ctx.add(c.Label(ret_label))
		self.ctx.add(c.Assignment('=', c.ID('__jmp_ctx__'), c.ID('NULL')))
		return False


	def _delete_name(self, target):
		assert isinstance(target, py.Name)
		scope = target.hl.parent
		scope.ll.del_attr_string(str(target))


	def _store_any(self, node, src_inst):
		if isinstance(node, py.Attribute):
			o = self.visit(node.value)
			o.set_attr_string(str(node.attr), src_inst)
		elif isinstance(node, py.Subscript):
			o = self.visit(node.value)
			if isinstance(node.slice, py.Slice):
				start, end, step = self.visit(node.slice)
				o.sequence_set_slice(start, end, step, src_inst)
			else:
				i = self.visit(node.slice)
				o.set_item(i, src_inst)
		elif isinstance(node, py.Name):
			self._store_name(node, src_inst)
		elif isinstance(node, (py.Tuple, py.List)):
			key = PyIntegerLL(None, self)
			key.declare()
			for i, elt in enumerate(node.elts):
				key.set_constant(i)
				tmp = src_inst.get_item(key)
				self._store_any(elt, tmp)
		else:
			raise NotImplementedError("Don't know how to assign to type: {}".format(type(node)))


	def _load_any(self, source):
		if isinstance(source, py.Name):
			tgt_inst = self._load_name(source)
		elif isinstance(source, py.Subscript):
			o = self.visit(source.value)
			#FIXME: this could be a slice
			i = self.visit(source.slice)
			tgt_inst = o.get_item(i)
		else:
			tgt_inst = self.visit(source)

		return tgt_inst


	def _store_name(self, target, val, scope=None):
		'''
		Common "normal" assignment handler.  Things like for-loop targets and with-stmt vars 
			need the same full suite of potential assignment targets as normal assignments.  With
			the caveat that only assignment will have non-Name children.
		
		target -- the node that is the lhs of the storage
		val -- the low-level object that will get set on it
		scope -- defaults to the parent of the symbol, but sometimes we need to assign into a different scope.
		'''
		assert isinstance(target, py.Name)

		# NOTE: the hl Name or Ref will always be parented under the right scope
		scope = target.hl.parent
		scope.ll.set_attr_string(str(target), val)

		# Note: some nodes do not get a visit_Name pass, since we don't have any preceding rhs for the assignment
		#		where we can correctly or easily get the type, 'as' or 'class', etc.  In these cases, we can just retrofit the
		#		value we actually created into the ll target for the hl slot so that future users of the hl instance will be able
		#		to find the correct ll name to use, rather than re-creating it when that users happens to visit_Name on the
		#		node with a missing ll slot.
		if not scope.symbols[str(target)].ll:
			scope.symbols[str(target)].ll = val


	def _load_name(self, source):
		'''
		source - the underlying name reference that we need to provide access to
		'''
		tmp = PyObjectLL(None, self)
		tmp.declare()

		# if we have a scope, load from it
		if source.hl.parent.ll:
			source.hl.parent.ll.get_attr_string(str(source), tmp)
		# otherwise, load from the global scope
		else:
			self.ll_module.get_attr_string(str(source), tmp)
		return tmp



	def visit_Assert(self, node):
		inst = self.visit(node.test)
		istrue_inst = inst.is_true()
		check = self.ctx.add(c.If(c.UnaryOp('!', c.ID(istrue_inst.name)), c.Compound(), None))
		with self.new_context(check.iftrue):
			if not node.msg:
				s = None
			elif isinstance(node.msg, py.Str):
				s = PyStringType.dequote(node.msg.s)
			else:
				inst = self.visit(node.msg)
				s = inst.str()
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
			inst.declare()

		self.comment('Load Attribute "{}.{}"'.format(str(node.value), str(node.attr)))
		if node.ctx == py.Store or node.ctx == py.Aug:
			# load the lhs object into the local c scope
			if isinstance(node.value, py.Name):
				lhs = self._load_name(node.value)
			else:
				lhs = self.visit(node.value)

			# load the attr off of the lhs, for use as a storage target
			lhs.get_attr_string(str(node.attr), inst)
			return inst

		elif node.ctx == py.Load:
			# load the attr lhs as normal
			if isinstance(node.value, py.Name):
				lhs = self._load_name(node.value)
			else:
				lhs = self.visit(node.value)

			# store the attr value into a local tmp variable
			lhs.get_attr_string(str(node.attr), inst)
			return inst

		else:
			raise NotImplementedError("Unknown Attribute access context: {}".format(node.ctx))


	def visit_AugAssign(self, node):
		self.comment('AugAssign: {} {} {}'.format(str(node.target), self.AUGASSIGN_PRETTY[node.op], str(node.value)))
		val_inst = self.visit(node.value)
		tgt_inst = self._load_any(node.target)

		# get the intermediate instance
		out_inst = self.create_ll_instance(node.hl)
		out_inst.declare()

		# perform the op, either returning a copy or getting a new instance
		if node.op == py.BitOr:
			tgt_inst.inplace_bitor(val_inst, out_inst)
		elif node.op == py.BitXor:
			tgt_inst.inplace_bitxor(val_inst, out_inst)
		elif node.op == py.BitAnd:
			tgt_inst.inplace_bitand(val_inst, out_inst)
		elif node.op == py.LShift:
			tgt_inst.inplace_lshift(val_inst, out_inst)
		elif node.op == py.RShift:
			tgt_inst.inplace_rshift(val_inst, out_inst)
		elif node.op == py.Add:
			tgt_inst.inplace_add(val_inst, out_inst)
		elif node.op == py.Sub:
			tgt_inst.inplace_subtract(val_inst, out_inst)
		elif node.op == py.Mult:
			tgt_inst.inplace_multiply(val_inst, out_inst)
		elif node.op == py.Div:
			tgt_inst.inplace_divide(val_inst, out_inst)
		elif node.op == py.FloorDiv:
			tgt_inst.inplace_floor_divide(val_inst, out_inst)
		elif node.op == py.Mod:
			tgt_inst.inplace_modulus(val_inst, out_inst)
		elif node.op == py.Pow:
			tgt_inst.inplace_power(val_inst, out_inst)

		self._store_any(node.target, out_inst)
		return out_inst


	def visit_BinOp(self, node):
		l = self.visit(node.left)
		r = self.visit(node.right)

		inst = self.create_ll_instance(node.hl)
		inst.declare()

		#TODO: python detects str + str at runtime and skips dispatch through PyNumber_Add, so we can 
		#		assume that would be faster
		if node.op == py.BitOr:
			l.bitor(r, inst)
		elif node.op == py.BitXor:
			l.bitxor(r, inst)
		elif node.op == py.BitAnd:
			l.bitand(r, inst)
		elif node.op == py.LShift:
			l.lshift(r, inst)
		elif node.op == py.RShift:
			l.rshift(r, inst)
		elif node.op == py.Add:
			l.add(r, inst)
		elif node.op == py.Sub:
			l.subtract(r, inst)
		elif node.op == py.Mult:
			l.multiply(r, inst)
		elif node.op == py.Div:
			l.divide(r, inst)
		elif node.op == py.FloorDiv:
			l.floor_divide(r, inst)
		elif node.op == py.Mod:
			l.modulus(r, inst)
		elif node.op == py.Pow:
			l.power(r, inst)
		else:
			raise NotImplementedError("BinOp({})".format(node.op))

		return inst


	def visit_BoolOp(self, node):
		self.comment('Boolop {}'.format((' ' + self.BOOLOPS_PRETTY[node.op] + ' ').join([str(v) for v in node.values])))

		out = PyObjectLL(None, self)
		out.declare(name="_boolop_res")

		tmp = CIntegerLL(None, self, is_a_bool=True)
		tmp.declare(init=0)
		# Note: need to re-initialize manually so that use in a loop starts with a default of 0 every time
		self.ctx.add(c.Assignment('=', c.ID(tmp.name), c.Constant('integer', 0)))

		# store base context, for restore, since we can't use with stmts here
		base_context = self.ctx

		# visit each value in order... nest so that we will automatically fall out on failure
		for value in node.values:
			val_inst = self.visit(value)
			val_inst.is_true(tmp)

			# Note: our last output is our actual result for both And and Or, since we only get to the last
			#		op if all of our others have been True or False respectively.
			if value is not node.values[-1]:
				# continue to next only if we are False
				if node.op == py.Or:
					ifstmt = self.ctx.add(c.If(c.UnaryOp('!', c.ID(tmp.name)), c.Compound(), c.Compound()))

				# continue to next only if we are True
				elif node.op == py.And:
					ifstmt = self.ctx.add(c.If(c.ID(tmp.name), c.Compound(), c.Compound()))

				# start next comparision in this (failed) context
				self.ctx = ifstmt.iftrue

				# if we are not continuing (the stmt is false) then assign our output
				with self.new_context(ifstmt.iffalse):
					val_inst = val_inst.as_pyobject()
					out.assign_name(val_inst)
			else:
				val_inst = val_inst.as_pyobject()
				out.assign_name(val_inst)

		# restore prior context
		self.ctx = base_context

		return out


	def visit_Bytes(self, node):
		inst = self.create_ll_instance(node.hl)
		inst.declare()
		inst.new(PyStringType.dequote(node.s))
		return inst


	def visit_Break(self, node):
		self.comment('break')
		def break_handler(label): # the next break is our ultimate target
			var = self.loop_vars[-1]
			if var: var.decref() # NOTE: cleanup the loop variable
			self.clear_exception()
			self.ctx.add(c.Goto(label))
			return True
		self.handle_flowcontrol(break_handler=break_handler)



	def visit_Call(self, node):
		def _call_super(self, node, funcinst):
			#FIXME: what if we call through a variable?
			#FIXME: what happens if we write to __class__ at runtime?

			# get the class type and the instance
			cls = self.find_nearest_class_scope(err='super must be called in a class context: {}'.format(node.start))
			fn = self.find_nearest_method_scope(err='super must be called in a method context: {}'.format(node.start))

			args = PyTupleLL(None, self)
			args.declare(name='__auto_super_call_args')
			args.pack(cls.ll.c_obj, fn.ll.get_self_accessor())

			# do the actual call
			rv = PyObjectLL(None, self)
			rv.declare()
			funcinst.call(args, None, rv)
			return rv

		def _call_builtin(self, node, funcinst):
			raise NotImplementedError

		def _call_local(self, node, funcinst):
			raise NotImplementedError

		def _call_remote(self, node, funcinst):
			# if we are calling super with no args, we need to provide them, since this is the framework's responsibility
			if node.func.hl and node.func.hl.name == 'super' and not node.args:
				return _call_super(self, node, funcinst)

			# build the arg tuple
			args_insts = []
			if node.args:
				for arg in node.args:
					idinst = self.visit(arg)
					idinst = idinst.as_pyobject()
					args_insts.append(idinst)

			# Note: we always need to pass a tuple as args, even if there is nothing in it
			if not node.starargs:
				args1 = PyTupleLL(None, self)
				args1.declare(name='args')
				args1.pack(*args_insts)
			else:
				args0 = PyListLL(None, self)
				args0.declare()
				args0.pack(*args_insts)
				va_inst = self.visit(node.starargs)
				args0_0 = args0.sequence_inplace_concat(va_inst)
				args0.clear()
				args1 = args0_0.sequence_as_tuple()
				args0_0.clear()

			# build the keyword dict
			args2 = None
			kw_insts = []
			if node.keywords or node.kwargs:
				for kw in node.keywords:
					valinst = self.visit(kw.value)
					valinst = valinst.as_pyobject()
					kw_insts.append((str(kw.keyword), valinst))
				if kw_insts or node.kwargs:
					args2 = PyDictLL(None, self)
					args2.declare()
					args2.new()
					if kw_insts:
						for keyname, valinst in kw_insts:
							args2.set_item_string(keyname, valinst)
					if node.kwargs:
						kwargs_inst = self.visit(node.kwargs)
						args2.update(kwargs_inst)

			# begin call output
			self.comment('do call "{}"'.format(str(node.func)))

			# make the call
			rv = PyObjectLL(None, self)
			rv.declare()
			funcinst.call(args1, args2, rv)

			# cleanup the args
			args1.clear()
			if args2: args2.clear()

			return rv

		#TODO: direct calling
		#TODO: track "type" so we can dispatch to PyCFunction_Call or PyFunction_Call instead of PyObject_Call 
		#TODO: track all call methods (callsite usage types) and see if we can't unpack into a direct c call

		# begin call output
		self.comment('Call function "{}"'.format(str(node.func)))

		# prepare the func name node
		funcinst = self.visit(node.func)

		# if we are defined locally, we can know the expected calling proc and reorganize our args to it
		#if node.func.hl and node.func.hl.scope:
		#	return _call_local(self, node, funcinst)
		#else:
		#	return _call_remote(self, node, funcinst)
		with self.scope.ll.maybe_recursive_call():
			ty = node.hl.get_type()
			ct = ty.call_type if isinstance(ty, PyFunctionType) else PyFunctionType.CALL_TYPE_UNKNOWN
			if ct == PyFunctionType.CALL_TYPE_LOCAL:
				rv = _call_local(self, node, funcinst)
			elif ct == PyFunctionType.CALL_TYPE_BUILTIN:
				rv = _call_builtin(self, node, funcinst)
			else:
				rv = _call_remote(self, node, funcinst)

		return rv


	def visit_ClassDef(self, node):
		# declare
		docstring, body = self.split_docstring(node.body)
		inst = self.create_ll_instance(node.hl)
		inst.create_builderfunc()
		pyclass_inst = inst.declare_pyclass()

		# build the class setup -- this has the side-effect of building all other module-level stuff before
		#	we do the class setup
		with self.new_scope(node.hl, inst.c_builder_func.body):
			# TODO: we should reserve these names in the LL builder
			self_inst = PyObjectLL(None, self)
			self_inst.name = self.scope.ctx.reserve_name('self', self.tu)
			args_tuple = PyTupleLL(None, self)
			args_tuple.name = self.scope.ctx.reserve_name('args', self.tu)
			kwargs_dict = PyDictLL(None, self)
			kwargs_dict.name = self.scope.ctx.reserve_name('kwargs', self.tu)

			# unpack the namespace dict that we will be writing to
			namespace_inst = PyDictLL(None, self)
			namespace_inst.declare(name='namespace')
			args_tuple.get_unchecked(0, namespace_inst)
			namespace_inst.fail_if_null(namespace_inst.name)
			namespace_inst.incref()

			inst.set_namespace(namespace_inst)

			inst.intro(docstring, '__main__' if self.hl_module.is_main else self.hl_module.owner.python_name)
			self.visit_nodelist(body)
			inst.outro()

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
		c_name_str.declare(name=str(node.name) + '_name')
		c_name_str.new(str(node.name))

		pyfunc = inst.create_builder_funcdef()

		build_class_inst = PyObjectLL(None, self)
		build_class_inst.declare()
		self.builtins.get_attr_string('__build_class__', build_class_inst)

		base_insts = []
		if node.bases:
			for b in node.bases:
				base_insts.append(self.visit(b))

		args = PyTupleLL(None, self)
		args.declare()
		args.pack(pyfunc, c_name_str, *base_insts)
		build_class_inst.call(args, node.kwargs, pyclass_inst)

		# apply decorators to the class
		for decoinst in deco_fn_insts:
			decoargs = PyTupleLL(None, self)
			decoargs.declare()
			decoargs.pack(pyclass_inst)
			decoinst.call(decoargs, None, pyclass_inst)

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
		out.declare(init=0)

		# Note: we need to initialize the output variable to 0 before the compare since compare can be
		#		used in, for instance, loops, where we need to re-do the comparison correctly every time.
		self.ctx.add(c.Assignment('=', c.ID(out.name), c.Constant('integer', 0)))

		# store this because when we bail we will come all the way back to our starting context at once
		base_context = self.ctx

		# make each comparison in order
		a = self.visit(node.left)
		a = a.as_pyobject()
		for op, b in zip(node.ops, node.comparators):
			b = self.visit(b)
			b = b.as_pyobject()

			# do one compare; only continue to next scope if we succeed
			if op in self.COMPARATORS_RICH:
				rv = a.rich_compare_bool(b, self.COMPARATORS_RICH[op])
			elif op == py.In:
				rv = b.sequence_contains(a)
			elif op == py.NotIn:
				rv = b.sequence_contains(a)
				rv = rv.not_()
			elif op == py.Is:
				rv = a.is_(b)
			elif op == py.IsNot:
				rv = a.is_(b)
				rv = rv.not_()
			else:
				raise NotImplementedError("unimplemented comparator in visit_compare: {}".format(op))
			stmt = c.If(c.ID(rv.name), c.Compound(), None)
			self.ctx.add(stmt)
			self.ctx = stmt.iftrue

			# next lhs is current rhs
			a = b

		# we are in our deepest nested context now, where all prior statements have been true
		self.ctx.add(c.Assignment('=', c.ID(out.name), c.Constant('integer', 1)))

		# reset the context
		self.ctx = base_context

		return out


	def visit_Continue(self, node):
		self.comment('continue')
		def loop_handler(label):
			self.ctx.add(c.Goto(label))
			return True
		self.handle_flowcontrol(continue_handler=loop_handler)


	def visit_Delete(self, node):
		#FIXME: move to _del_any?
		for target in node.targets:
			if isinstance(target, py.Name):
				self._delete_name(target)
			elif isinstance(target, py.Attribute):
				inst = self.visit(target.value)
				inst.del_attr_string(str(target.attr))
			elif isinstance(target, py.Subscript):
				ovalue = self.visit(target.value)
				if isinstance(target.slice, py.Slice):
					start_inst, end_inst, step_inst = self.visit(target.slice)
					ovalue.sequence_del_slice(start_inst, end_inst, step_inst)
				else:
					kvalue = self.visit(target.slice)
					ovalue.del_item(kvalue)
			else:
				raise NotImplementedError("Unknown deletion type")


	def visit_Dict(self, node):
		inst = self.create_ll_instance(node.hl)
		inst.declare()
		inst.new()
		if node.keys and node.values:
			for k, v in zip(node.keys, node.values):
				kinst = self.visit(k)
				vinst = self.visit(v)
				inst.set_item(kinst, vinst)
		return inst


	def visit_Ellipsis(self, node):
		#FIXME: get a ref to the ellipsis object at startup and incref and return it here
		raise NotImplementedError


	def visit_Expr(self, node):
		return self.visit(node.value)


	def visit_ExtSlice(self, node):
		#FIXME: figure out what these are exactly... 
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
		iter.declare()
		iter_obj.get_iter(iter)

		# the gets the object locally inside of the while expr; we do the full assignment inside the body
		self.loop_vars.append(PyObjectLL(None, self))
		self.loop_vars[-1].declare()
		stmt = self.ctx.add(c.While(c.Assignment('=', c.ID(self.loop_vars[-1].name), c.FuncCall(c.ID('PyIter_Next'), c.ExprList(c.ID(iter.name)))), c.Compound()))
		with self.new_context(stmt.stmt):
			with self.new_label(break_label), self.new_label(continue_label):
				self._store_any(node.target, self.loop_vars[-1])
				self.visit_nodelist(node.body)
			self.ctx.add(c.Label(continue_label))
			self.loop_vars[-1].decref()
		self.loop_vars.pop()

		# handle the no-break case: else
		# if we don't jump to forloop, then we need to just run the else block
		self.visit_nodelist(node.orelse)

		# after else, we get the break target
		self.ctx.add(c.Label(break_label))


	def visit_FunctionDef(self, node):
		# for use everywhere else in this function when we need to pass our entire args descriptor down to the implementor
		full_args = (node.args.args or [], node.args.vararg, node.args.kwonlyargs or [], node.args.kwarg)

		# prepare the lowlevel
		docstring, body = self.split_docstring(node.body)
		inst = self.create_ll_instance(node.hl)
		inst.prepare()
		inst.create_pystubfunc()
		inst.create_runnerfunc(*full_args)

		self.comment("Build function {}".format(str(node.name)))
		pycfunc = inst.declare_function_object(docstring)

		# enumerate and attach defaults and keyword defaults
		inst.attach_defaults(
							[self.visit(default) for default in (node.args.defaults or [])],
					 		[(str(arg.arg), self.visit(kwdefault)) for arg, kwdefault in \
									(zip(node.args.kwonlyargs, node.args.kw_defaults))] \
									if node.args.kw_defaults else [])
		# attach annotations to the pycfunction instance
		inst.attach_annotations(self.visit(node.returns) if hasattr(node, 'returns') else None,
							[(str(a.arg), self.visit(a.annotation)) for a in node.args.args] if node.args.args else [],
							str(node.args.vararg), self.visit(node.args.varargannotation),
							[(str(a.arg), self.visit(a.annotation)) for a in node.args.kwonlyargs] if node.args.kwonlyargs else [],
							str(node.args.kwarg), self.visit(node.args.kwargannotation))

		# visit any decorators (e.g. run decorators with args to get real decorators _before_ defining the function)
		deco_fn_insts = [self.visit(dn) for dn in reversed(node.decorator_list or [])] if hasattr(node, 'decorator_list') else []

		# Build the python stub function
		with self.new_scope(node.hl, inst.c_pystub_func.body):
			self.comment('Python interface stub function "{}"'.format(str(node.name)))
			inst.stub_intro()

			# Attach all parameters and names into the local namespace
			# We can't know the convention the caller used, so we need to handle all 
			#  possiblities -- local callers do their own setup and just call the runner.
			inst.stub_load_args(node.args.args or [], node.args.defaults or [],
								node.args.vararg,
								node.args.kwonlyargs or [], node.args.kw_defaults or [],
								node.args.kwarg)

			# call the low-level runner function from the stub
			inst.transfer_to_runnerfunc(*full_args)

			# emit cleanup and return code
			inst.stub_outro()

		# build the actual runner function
		with self.new_scope(node.hl, inst.c_runner_func.body):
			inst.runner_intro()
			inst.runner_load_args(*full_args)
			inst.runner_load_locals()
			self.comment('body')
			self.visit_nodelist(body)
			inst.runner_outro()

		# apply any decorators
		tmp = pycfunc
		if deco_fn_insts:
			self.comment('decorate {}'.format(str(node.name)))
			tmp = PyObjectLL(None, self)
			tmp.declare()
			tmp.assign_name(pycfunc)
			for decoinst in deco_fn_insts:
				#NOTE: We need to use a tmp var for these so that the returned function does not overwrite the
				#		global pycfunc pointer because, even if the @wraps is used, we lose the __defaults__ and __kwdefaults__
				#		and cannot load them correctly later in the stub.
				decoargs = PyTupleLL(None, self)
				decoargs.declare()
				decoargs.pack(tmp)
				decoinst.call(decoargs, None, tmp)

		# store the resulting function into the scope where it's defined
		if not node.hl.is_anonymous:
			self.comment('store function name into scope')
			self._store_name(node.name, tmp)
		inst.name = inst.c_obj.name

		return inst

	visit_Lambda = visit_FunctionDef


	def visit_GeneratorExp(self, node):
		full_args = ([], None, [], None)
		docstring = None

		# prepare the lowlevel
		inst = self.create_ll_instance(node.hl)
		inst.prepare()
		inst.create_pystubfunc()
		inst.create_runnerfunc(*full_args)

		self.comment("Build function {}".format(str(node.name)))
		pycfunc = inst.declare_function_object(docstring)
		# NOTE: doing the call here will xdecref the target (us) before assignment, so avoid freeing ourself
		pycfunc.incref()
		# NOTE: we don't really care about the generator _function_, we just want the underlying generator
		pycfunc.call(None, None, pycfunc)

		# Build the python stub function
		with self.new_scope(node.hl, inst.c_pystub_func.body):
			self.comment('Python interface stub function "{}"'.format(str(node.name)))
			inst.stub_intro()
			inst.transfer_to_runnerfunc(*full_args)
			inst.stub_outro()

		# build the actual runner function
		with self.new_scope(node.hl, inst.c_runner_func.body):
			inst.runner_intro()
			inst.runner_load_args(*full_args)
			inst.runner_load_locals()
			self.comment('body')
			def _set():
				obj = self.visit(node.elt)
				self.scope.ll.do_yield(obj)
			self.visit_comp_generators(node.generators, _set)
			inst.runner_outro()

		# store the resulting function into the scope where it's defined
		if not node.hl.is_anonymous:
			self.comment('store function name into scope')
			self._store_name(node.name, pycfunc)
		inst.name = inst.c_obj.name

		return inst


	#def visit_Global(self, node):
	#	not needed


	def visit_If(self, node):
		inst = self.visit(node.test)
		if isinstance(inst, PyObjectLL):
			tmpvar = inst.is_true()
			test = c.BinaryOp('==', c.Constant('integer', 1), c.ID(tmpvar.name))
		elif isinstance(inst, CIntegerLL):
			test = c.ID(inst.name)
		else:
			raise NotImplementedError('Non-pyobject as value for If test')

		stmt = self.ctx.add(c.If(test, c.Compound(), c.Compound() if node.orelse else None))
		with self.new_context(stmt.iftrue):
			self.visit_nodelist(node.body)
		if node.orelse:
			with self.new_context(stmt.iffalse):
				self.visit_nodelist(node.orelse)


	def visit_IfExp(self, node):
		out_inst = PyObjectLL(None, self)
		out_inst.declare(name="_ifexp_rv")

		tst_inst = self.visit(node.test)
		tst_is_true = tst_inst.is_true()
		ifstmt = self.ctx.add(c.If(c.ID(tst_is_true.name), c.Compound(), c.Compound()))
		with self.new_context(ifstmt.iftrue):
			inst = self.visit(node.body)
			out_inst.assign_name(inst)
		with self.new_context(ifstmt.iffalse):
			inst = self.visit(node.orelse)
			out_inst.assign_name(inst)

		return out_inst


	def _import_module(self, module, fullname):
		tmp = PyObjectLL(None, self)
		tmp.declare()
		if module.modtype == MelanoModule.PROJECT:
			# call the builder function to construct or access the module
			self.comment("Import local module {}".format(str(module.python_name)))
			self.ctx.add(c.Assignment('=', c.ID(tmp.name), c.FuncCall(c.ID(module.ll.c_builder_name), c.ExprList())))
		else:
			# import the module at the c level
			self.comment("Import external module {}".format(str(module.python_name)))
			self.ctx.add(c.Assignment('=', c.ID(tmp.name), c.FuncCall(c.ID('PyImport_ImportModule'), c.ExprList(
																												c.Constant('string', fullname)))))
		tmp.fail_if_null(tmp.name)
		tmp.incref()
		return tmp


	def visit_Import(self, node):
		def _import_as_name(self, node, name, asname):
			ref = asname.hl.scope
			assert ref is not None
			tgt = self.visit(asname)
			tmp = self._import_module(ref, str(name))
			self.comment("store imported '{}' as '{}'".format(str(name), str(asname)))
			self._store_name(asname, tmp)

		def _import_name(self, node, name):
			ref = name.hl.scope
			tgt = self.visit(name)
			assert ref is not None
			tmp = self._import_module(ref, str(name))
			self._store_name(name, tmp)

		def _import_attribute(self, node, attr):
			parts = []
			prior = None
			for name in attr.get_names():
				ref = name.hl.scope
				tgt = self.visit(name)
				assert ref is not None

				parts.append(str(name))
				fullname = '.'.join(parts)

				# import the next part of the name
				tmp = self._import_module(ref, fullname)

				# subsequent sets are in the wrong dict... how does this decide where to set attrs?
				if name is attr.first():
					self._store_name(name, tmp)
				else:
					prior.set_attr_string(str(name), tmp)

				prior = tmp

		for alias in node.names:
			if alias.asname:
				_import_as_name(self, node, alias.name, alias.asname)
			else:
				if isinstance(alias.name, py.Name):
					_import_name(self, node, alias.name)
				else:
					_import_attribute(self, node, alias.name)


	def visit_ImportFrom(self, node):
		mod = node.module.hl
		base_module_inst = self._import_module(mod, mod.python_name)

		# pluck names out of the module and into our namespace
		def _import_name(name, from_module_inst):
			# load the name off of the module
			val = PyObjectLL(None, self)
			val.declare()
			from_module_inst.get_attr_string(PyStringLL.name_to_c_string(str(name)), val)
			val.fail_if_null(val.name)
			return val

		for alias in node.names:
			# handle star names separately
			if str(alias.name) == '*':
				for name in mod.lookup_star():
					py_name = py.Name(name, py.Store, None)
					py_name.hl = self.scope.symbols[name]
					val = _import_name(py_name, base_module_inst)
					self._store_name(py_name, val)
				continue

			# get the reference -- hl is always stored on the name by the indexer
			if isinstance(alias.name.hl, NameRef) and isinstance(alias.name.hl.ref, MelanoModule):
				val = self._import_module(alias.name.hl.ref, alias.name.hl.ref.python_name)
			else:
				val = _import_name(alias.name, base_module_inst)

			# store the name or asname as needed
			if alias.asname:
				self._store_name(alias.asname, val)
			else:
				self._store_name(alias.name, val)


	def visit_Index(self, node):
		#NOTE: Pass through index values... not sure why python ast wraps these rather than just having a value.
		node.hl = node.value.hl
		node.hl.ll = self.visit(node.value)
		return node.hl.ll


	#def visit_Lambda(self, node):
	#	See visit_FunctionDef for actual implementation


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
		self.ll_module.declare()

		# set the initial context
		with self.new_context(self.ll_module.c_builder_func.body):
			with self.module_scope(self.hl_module, self.ctx):
				with self.new_label('end'):
					# setup the module
					self.ll_module.return_existing()
					self.ll_module.new()
					self.ll_module.intro()

					# visit all children
					# load and attach special attributes to the module dict
					self.ll_module.set_initial_string_attribute('__file__', self.hl_module.filename)
					docstring, body = self.split_docstring(node.body)
					self.ll_module.set_initial_string_attribute('__doc__', docstring)
					sym = node.hl.get_symbol('__doc__').name = docstring

					# record the top-level context in the scope, so we can declare toplevel variables when in a sub-contexts
					self.scope.ctx = self.ctx

					# visit all children
					self.visit_nodelist(body)

				# cleanup and return
				self.ll_module.outro()

		# the only module we want to load automatically at runtime is the main module
		if self.hl_module.is_main:
			with self.main_scope():
				tmp = PyObjectLL(None, self)
				tmp.declare(name="_main_")
				self.main.body.add(c.Assignment('=', c.ID(tmp.name), c.FuncCall(c.ID(self.ll_module.c_builder_name), c.ExprList())))
				self.main.body.add(c.If(c.UnaryOp('!', c.ID(tmp.name)), c.Compound(
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
				inst.declare()
			return node.hl.ll

		# if we are loading a name, we have to search for the name's location
		elif node.ctx == py.Load:
			return self._load_name(node)

		else:
			raise NotImplementedError("unknown context for name: {}".format(node.ctx))


	#def visit_NonLocal(self, node):
	#	Not needed


	def visit_Num(self, node):
		if not node.hl.ll:
			inst = self.create_ll_instance(node.hl)
			inst.declare()
		else:
			inst = node.hl.ll
		inst.new(node.n)
		return inst


	def visit_Pass(self, node):
		self.comment('pass')


	def visit_Raise(self, node):
		self.comment('raise')

		if not node.exc:
			exc_cookie = self.exc_cookie_stack[-1]
			self.restore_exception(exc_cookie)
			self.exc_cookie_stack.append(exc_cookie)
			self.handle_flowcontrol(except_handler=self._except_flowcontrol)
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
		is_a_type = inst.is_instance(PyTypeLL)
		if_stmt = self.ctx.add(c.If(c.ID(is_a_type.name), c.Compound(), c.Compound()))
		with self.new_context(if_stmt.iftrue):
			self.set_exception(inst, None)
		with self.new_context(if_stmt.iffalse):
			#TODO: move into get_type
			ty_inst = PyTypeLL(None, self)
			ty_inst.declare()
			inst.get_type(ty_inst)
			self.set_exception(ty_inst, inst)
		self.capture_error()
		self.exit_with_exception()

		# do exception flow-control
		self.handle_flowcontrol(except_handler=self._except_flowcontrol)


	def visit_Return(self, node):
		# get the return value for when we exit
		if node.value:
			inst = self.visit(node.value)
			inst = inst.as_pyobject()
			self.ctx.add(c.Assignment('=', c.ID('__return_value__'), c.ID(inst.name)))
		else:
			self.ctx.add(c.Assignment('=', c.ID('__return_value__'), c.ID(self.none.name)))
		self.ctx.add(c.FuncCall(c.ID('Py_INCREF'), c.ExprList(c.ID('__return_value__'))))

		# do exit flowcontrol to handle finally blocks
		self.handle_flowcontrol()


	def visit_Set(self, node):
		inst = self.create_ll_instance(node.hl)
		inst.declare()
		inst.new(None)
		for v in node.elts:
			vinst = self.visit(v)
			inst.add(vinst)
		return inst


	def visit_Slice(self, node):
		start = end = step = None
		if node.lower:
			start = self.visit(node.lower)
		if node.upper:
			end = self.visit(node.upper)
		if node.step:
			step = self.visit(node.step)
		return start, end, step


	def visit_Starred(self, node):
		#FIXME: we probably want to handle this up in _store_any for tuples, mostly
		raise NotImplementedError


	def visit_Str(self, node):
		inst = self.create_ll_instance(node.hl)
		inst.declare()
		inst.new(PyStringType.dequote(node.s))
		return inst


	def visit_Subscript(self, node):
		if node.ctx == py.Store:
			raise SystemError("Subscript store needs special casing at assignment site")
		elif node.ctx in [py.Load, py.Aug]:
			tgtinst = self.visit(node.value)
			if isinstance(node.slice, py.Slice):
				start_inst, end_inst, step_inst = self.visit(node.slice)
				out = tgtinst.sequence_get_slice(start_inst, end_inst, step_inst)
				return out
			else:
				kinst = self.visit(node.slice)
				tmp = PyObjectLL(None, self)
				tmp.declare()
				tgtinst.get_item(kinst, tmp)
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
		self.ctx.add(c.Goto(tryend_label))

		# branch target for jumping to this exception
		self.ctx.add(c.Label(except_label))

		### exception dispatch logic
		## Check if there was actually an exception -- raise if not
		exc_type_inst = PyObjectLL(None, self)
		exc_type_inst.declare()
		self.ctx.add(c.Assignment('=', c.ID(exc_type_inst.name), c.FuncCall(c.ID('PyErr_Occurred'), c.ExprList())))
		exc_type_inst.fail_if_null(exc_type_inst.name)
		exc_type_inst.incref()
		## Store the exception during exception processing
		with self.save_exception() as exc_cookie:
			## check the exception handles against the exception that occurred
			parts = [] # [c.If]
			for handler in node.handlers:
				if handler.type:
					# build list of exceptions to check at this handler
					matchers = []
					if isinstance(handler.type, py.Tuple):
						for name in handler.type.elts:
							class_inst = self.visit(name)
							matchers.append(c.FuncCall(c.ID('PyErr_GivenExceptionMatches'), c.ExprList(c.ID(exc_type_inst.name), c.ID(class_inst.name))))
					elif isinstance(handler.type, py.Name):
						class_inst = self.visit(handler.type)
						matchers.append(c.FuncCall(c.ID('PyErr_GivenExceptionMatches'), c.ExprList(c.ID(exc_type_inst.name), c.ID(class_inst.name))))
					else:
						raise NotImplementedError("Unknown type of exception handler")

					# build operation to check all of these at once, in order
					binop = matchers[0]
					for item in matchers[1:]:
						binop = c.BinaryOp('||', binop, item)
					test = c.If(binop, c.Compound(), None)

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
				#NOTE: if we get here we will be leaving, so we need to restore the exception before visiting this
				top_cookie = self.exc_cookie_stack[-1]
				self.restore_exception(top_cookie)
				self.exc_cookie_stack.append(top_cookie) # re-save so we can pop again at exit
				self.handle_flowcontrol(except_handler=self._except_flowcontrol)

			## add the if-chain to the body
			self.ctx.add(parts[0])

		# if we fall off the end of the exception handler, we are considered cleared
		self.clear_exception()
		self.ctx.add(c.Goto(tryelseend_label))

		# if we finish, successfully, jump here to skip the exeption handling and run the else block
		self.ctx.add(c.Label(tryend_label))
		self.visit_nodelist(node.orelse)

		# if we reach the end of the except block, don't run the else block
		self.ctx.add(c.Label(tryelseend_label))


	def visit_TryFinally(self, node):
		self.comment('try-finally')

		# add this finally to the flow control context in the try body
		label = self.scope.get_label('finally')
		with self.new_label(label):
			self.visit_nodelist(node.body)

		# branch target for jumping to a finally clause
		self.ctx.add(c.Label(label))

		# handle the final stmt
		with self.maybe_save_exception():
			self.visit_nodelist(node.finalbody)

		# if the top-level needs control back to complete, it will set __jmp_ctx__
		self.ctx.add(c.If(c.ID('__jmp_ctx__'), c.Compound(c.Goto(c.UnaryOp('*', c.ID('__jmp_ctx__')))), None))


	def visit_Tuple(self, node):
		if node.ctx in [py.Load, py.Aug]:
			inst = self.create_ll_instance(node.hl)
			inst.declare()
			to_pack = [self.visit(n) for n in node.elts] if node.elts else []
			inst.pack(*to_pack)
			return node.hl.ll
		else:
			tpl_inst = self.create_ll_instance(node.hl)
			tpl_inst.declare()


	visit_List = visit_Tuple


	def visit_While(self, node):
		# get a break and continue label
		break_label = self.scope.get_label('break_while')
		continue_label = self.scope.get_label('continue_while')

		self.loop_vars.append(None)

		# Note: we use a do{}while(1) with manual break, instead of the more direct while(){}, so that we only
		#		have to visit/emit the test code once, rather than once outside and once at the end of the loop.
		dowhile = c.DoWhile(c.Constant('integer', 1), c.Compound())
		self.ctx.add(dowhile)
		with self.new_context(dowhile.stmt):
			with self.new_label(break_label), self.new_label(continue_label):
				# perform the test
				test_inst = self.visit(node.test)
				#TODO: short circuit this somehow... make is_true for CIntegerLL perhaps?
				#			also fix in visit_If if we do work it out
				if isinstance(test_inst, PyObjectLL):
					tmpvar = test_inst.is_true()
					test = c.BinaryOp('==', c.Constant('integer', 0), c.ID(tmpvar.name))
				elif isinstance(test_inst, CIntegerLL):
					test = c.UnaryOp('!', c.ID(test_inst.name))
				else:
					raise NotImplementedError('Non-pyobject as value for If test')

				# exit if our test failed
				self.ctx.add(c.If(test, c.Compound(c.Break()), None))

				# do loop actions
				self.visit_nodelist(node.body)

			# continue on to immediately before test for continue
			self.ctx.add(c.Label(continue_label))

		self.loop_vars.pop()

		# add the non-break (at the python level, not the c level) case for else
		self.visit_nodelist(node.orelse)
		self.ctx.add(c.Label(break_label))


	def visit_With(self, node):
		ctx = self.visit(node.context_expr)

		# load enter and exit
		enter_fn_inst = PyObjectLL(None, self)
		enter_fn_inst.declare()
		ctx.get_attr_string('__enter__', enter_fn_inst)
		exit_fn_inst = PyObjectLL(None, self)
		exit_fn_inst.declare()
		ctx.get_attr_string('__exit__', exit_fn_inst)

		tmp = PyObjectLL(None, self)
		tmp.declare()

		# call enter
		args = PyTupleLL(None, self)
		args.declare()
		args.pack()
		enter_fn_inst.call(args, None, tmp)

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
		self.ctx.add(c.Label(exit_label))

		# query for a possibly set exception
		argvec, exc_cookie = self.maybe_save_exception_normalized_enter()

		# do the __exit__ call
		out_var = PyObjectLL(None, self)
		out_var.declare()
		exit_fn_inst.call(argvec, None, out_var)
		argvec.clear()

		# raise the exception if the output is False, otherwise supress
		suppress_inst = out_var.is_true()
		restore_if = self.ctx.add(c.If(c.UnaryOp('!', c.ID(suppress_inst.name)), c.Compound(), c.Compound()))
		with self.new_context(restore_if.iftrue):
			self.maybe_restore_exception_normalized_exit(exc_cookie)
		with self.new_context(restore_if.iffalse):
			self.clear_exception()

			# NOTE: just clearing an error isn't enough here: our flowcontrol handler will assume an exception will raise out
			#		of this context, so we need to also stop ourself from jumping out of this context.  Since the error is squashed
			#		we can just continue on our way.
			self.ctx.add(c.Assignment('=', c.ID('__jmp_ctx__'), c.ID('NULL')))

		# if the top-level needs control back to complete, it will set __jmp_ctx__
		self.declare_jump_context()
		self.ctx.add(c.If(c.ID('__jmp_ctx__'), c.Compound(c.Goto(c.UnaryOp('*', c.ID('__jmp_ctx__')))), None))


	def visit_UnaryOp(self, node):
		o = self.visit(node.operand)

		inst = PyObjectLL(None, self)
		inst.declare()

		if node.op == py.Invert:
			o.invert(inst)
		elif node.op == py.Not:
			tmp = o.not_()
			inst.assign_name(tmp.as_pyobject())
		elif node.op == py.UAdd:
			o.positive(inst)
		elif node.op == py.USub:
			o.negative(inst)
		else:
			raise NotImplementedError("UnaryOp({})".format(node.op))

		return inst


	def visit_Yield(self, node):
		# get the returned instance
		rv_inst = self.visit(node.value)
		self.scope.ll.do_yield(rv_inst)



	### Comprehensions ###
	def visit_comp_generators(self, generators, setter):
		node = generators[0]

		iter_obj = self.visit(node.iter)

		# get the PyIter for the iteration object
		iter = PyObjectLL(None, self)
		iter.declare()
		iter_obj.get_iter(iter)

		# the gets the object locally inside of the while expr; we do the full assignment inside the body
		tmp = PyObjectLL(None, self)
		tmp.declare()
		stmt = self.ctx.add(c.While(c.Assignment('=', c.ID(tmp.name), c.FuncCall(c.ID('PyIter_Next'), c.ExprList(c.ID(iter.name)))), c.Compound()))
		with self.new_context(stmt.stmt):
			# set this loops variable
			self._store_any(node.target, tmp)

			# if we have selectors on this generator, visit them recursively
			if node.ifs:
				rv = self.visit_comp_ifs(generators, 0, setter)
				tmp.decref()
				return rv

			# if we have more generators, visit them, otherwise set our targets
			if len(generators) > 1:
				rv = self.visit_comp_generators(generators[1:], setter)
				tmp.decref()
				return rv

			# if out of generators, go to setting our result
			setter()



	def visit_comp_ifs(self, generators, offset, setter):
		node = generators[0].ifs[offset]
		offset += 1

		# get our truth value for the test
		inst = self.visit(node)
		if isinstance(inst, PyObjectLL):
			tmpvar = inst.is_true()
			test = c.BinaryOp('==', c.Constant('integer', 1), c.ID(tmpvar.name))
		elif isinstance(inst, CIntegerLL):
			test = c.ID(inst.name)
		else:
			raise NotImplementedError('Non-pyobject as value for If test')

		# create the if stmt
		stmt = self.ctx.add(c.If(test, c.Compound(), None))
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
		dict_inst.prepare_locals()

		out = PyDictLL(None, self)
		out.declare(name="_dictcomp_")
		out.new()

		def _set():
			k_inst = self.visit(node.key)
			v_inst = self.visit(node.value)
			out.set_item(k_inst, v_inst)
		self.visit_comp_generators(node.generators, _set)

		return out


	def visit_ListComp(self, node):
		list_inst = self.create_ll_instance(node.hl)
		list_inst.prepare_locals()

		out_inst = PyListLL(None, self)
		out_inst.declare(name="_listcomp_")
		out_inst.new()

		def _set():
			obj = self.visit(node.elt)
			out_inst.append(obj)
		self.visit_comp_generators(node.generators, _set)

		return out_inst


	def visit_SetComp(self, node):
		set_inst = self.create_ll_instance(node.hl)
		set_inst.prepare_locals()

		out = PySetLL(None, self)
		out.declare(name="_setcomp_")
		out.new()

		def _set():
			obj = self.visit(node.elt)
			out.add(obj)
		self.visit_comp_generators(node.generators, _set)

		return out


