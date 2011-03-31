'''
Convert the low-level parse tree into a high-level Abstract Syntax Tree.

NOTES for Melano:
	- Copied and adapted from pypy; this involved a complete rewrite of many
		different elements to support new python3 constructs.
	- Passes the low-level Node to the ast nodes directly, rather than pulling
		off and passing start line and column individually.
	- Handles our skiptokens by filtering the children lists as needed.
'''
import melano.py.ast as ast


class PythonASTBuilder:
	'''Convert the low-level ast produced by parsing into a high-level ast
		useful for scanning, linting, etc.'''
	def __init__(self, parser):
		self.parser = parser

		class _Symbols: pass
		self.syms = _Symbols()
		for index, name in self.parser.grammar.symbol_names.items():
			setattr(self.syms, name, index)

		class _Tokens: pass
		self.tokens = _Symbols()
		for name, index in self.parser.grammar.TOKENS.items():
			setattr(self.tokens, name, index)

		self.SKIPTOKENS = {
				self.tokens.COMMENT,
				self.tokens.NL,
				self.tokens.NEWLINE,
				self.tokens.ENDMARKER}

		self.operator_map = {
			self.tokens.VBAR : ast.BitOr,
			self.tokens.CIRCUMFLEX : ast.BitXor,
			self.tokens.AMPER : ast.BitAnd,
			self.tokens.LEFTSHIFT : ast.LShift,
			self.tokens.RIGHTSHIFT : ast.RShift,
			self.tokens.PLUS : ast.Add,
			self.tokens.MINUS : ast.Sub,
			self.tokens.STAR : ast.Mult,
			self.tokens.SLASH : ast.Div,
			self.tokens.DOUBLESLASH : ast.FloorDiv,
			self.tokens.PERCENT : ast.Mod
		}

		self.augassign_operator_map = {
			'+='  : ast.Add,
			'-='  : ast.Sub,
			'/='  : ast.Div,
			'//=' : ast.FloorDiv,
			'%='  : ast.Mod,
			'<<='  : ast.LShift,
			'>>='  : ast.RShift,
			'&='  : ast.BitAnd,
			'|='  : ast.BitOr,
			'^='  : ast.BitXor,
			'*='  : ast.Mult,
			'**=' : ast.Pow
		}


	def type_name(self, ty):
		for index, name in self.parser.grammar.symbol_names.items():
			if index == ty:
				return name
		for name, index in self.parser.grammar.TOKENS.items():
			if index == ty:
				return name


	def build(self, node):
		assert node.type == self.syms.file_input

		children = self.children(node)
		stmts = []
		for stmt in children:
			ty = stmt.type
			if ty in self.SKIPTOKENS:
				continue
			if ty == self.syms.stmt:
				stmts.extend(self.handle_stmt(stmt))

		node.endpos = node.children[-1].endpos
		return ast.Module(stmts, node)


	def children(self, node):
		'''Return the 'real' children of a node -- e.g. filter skip-tokens.'''
		if not node.children:
			self.pretty_print(node)
		return [c for c in node.children if c.type not in self.SKIPTOKENS]


	def print_children(self, node):
		print('CHILD:', self.type_name(node.type))
		for c in node.children:
			print('\t' + self.type_name(c.type))
		print("END")


	def pretty_print(self, node, level=0):
		pad = '\t' * level
		print(pad + self.type_name(node.type) + ' [' + str(node.value).strip() + ']')
		if node.children:
			for c in node.children:
				self.pretty_print(c, level + 1)


	def set_context(self, expr, ctx):
		"""Set the context of an expression to Store or Del if possible."""
		#try:
		expr.set_context(ctx)
		#except ast.UnacceptableExpressionContext as e:
		#	self.error_ast(e.msg, e.node)
		#except misc.ForbiddenNameAssignment as e:
		#	self.error_ast("assignment to %s" % (e.name,), e.node)


	def handle_del_stmt(self, del_node):
		children = self.children(del_node)
		targets = self.handle_exprlist(children[1], ast.Del)
		if isinstance(targets, ast.Tuple):
			return ast.Delete(targets.elts, del_node)
		return ast.Delete([targets], del_node)


	def handle_flow_stmt(self, flow_node):
		first_child = self.children(flow_node)[0]
		first_child_type = first_child.type
		if first_child_type == self.syms.break_stmt:
			return ast.Break(flow_node)
		elif first_child_type == self.syms.continue_stmt:
			return ast.Continue(flow_node)
		elif first_child_type == self.syms.yield_stmt:
			children = self.children(first_child)
			yield_expr = self.handle_expr(children[0])
			return ast.Expr(yield_expr, flow_node)
		elif first_child_type == self.syms.return_stmt:
			children = self.children(first_child)
			if len(children) == 1:
				values = None
			else:
				values = self.handle_testlist(children[1])
			return ast.Return(values, flow_node)
		elif first_child_type == self.syms.raise_stmt:
			exc = None
			value = None
			children = self.children(first_child)
			if len(children) >= 2:
				exc = self.handle_expr(children[1])
			if len(children) >= 4:
				value = self.handle_expr(children[3])
			return ast.Raise(exc, value, flow_node)
		else:
			raise AssertionError("unknown flow statement")


	def handle_import_stmt(self, import_node):
		children = self.children(import_node)
		if children[0].type == self.syms.import_name:
			return self.handle_import_name(children[0])
		elif children[0].type == self.syms.import_from:
			return self.handle_import_from(children[0])
		else:
			raise AssertionError("unknown import node")


	def handle_import_name(self, import_name):
		children = self.children(import_name)
		assert children[0].value == 'import'
		aliases = self.handle_dotted_as_names(children[1])
		return ast.Import(aliases, import_name)


	def handle_import_from(self, import_from):
		children = self.children(import_from)
		at = 0
		assert children[at].value == 'from'
		at += 1
		level = 0
		while children[at].type in (self.tokens.DOT, self.tokens.ELLIPSIS):
			if children[at].type == self.tokens.DOT:
				level += 1
			elif children[at].type == self.tokens.ELLIPSIS:
				level += 3
			at += 1
		if children[at].type == self.syms.dotted_name:
			module = self.handle_dotted_name(children[at])
			at += 1
		else:
			module = ast.Name('', ast.Load, children[at])
		assert children[at].value == 'import'
		at += 1
		if children[at].type == self.syms.import_as_names:
			names = self.handle_import_as_names(children[at])
		elif children[at].type == self.tokens.STAR:
			names = [ast.alias(ast.Name("*", ast.Load, children[at]), None)]
		else:
			assert children[at].type == self.tokens.LPAR
			assert children[-1].type == self.tokens.RPAR
			at += 1
			names = self.handle_import_as_names(children[at])
		return ast.ImportFrom(module, names, level, import_from)


	def handle_import_as_names(self, import_as_names):
		children = self.children(import_as_names)
		aliases = []
		for child in children:
			if child.type == self.tokens.COMMA: continue
			alias = self.handle_import_as_name(child)
			aliases.append(alias)
		return aliases


	def handle_import_as_name(self, import_as_name):
		children = self.children(import_as_name)
		assert children[0].type == self.tokens.NAME
		name = ast.Name(children[0].value, ast.Store, children[0])
		asname = None
		if len(children) > 1:
			assert children[1].value == 'as'
			assert children[2].type == self.tokens.NAME
			asname = ast.Name(children[2].value, ast.Store, children[2])
			name.set_context(ast.Load)
		return ast.alias(name, asname)


	def handle_dotted_as_names(self, dotted_as_names):
		aliases = []
		for child in self.children(dotted_as_names):
			if child.type == self.tokens.COMMA: continue
			assert child.type == self.syms.dotted_as_name
			alias = self.handle_dotted_as_name(child)
			aliases.append(alias)
		return aliases


	def handle_dotted_as_name(self, dotted_as_name):
		children = self.children(dotted_as_name)
		name = self.handle_dotted_name(children[0])
		asname = None
		if len(children) > 1:
			assert children[1].value == 'as'
			assert children[2].type == self.tokens.NAME
			asname = ast.Name(children[2].value, ast.Store, children[2])
		else:
			name.set_context(ast.Store)
		return ast.alias(name, asname)


	def handle_global_stmt(self, global_node):
		children = self.children(global_node)
		names = [children[i].value for i in range(1, len(children), 2)]
		return ast.Global(names, global_node)


	def handle_nonlocal_stmt(self, nonlocal_node):
		children = self.children(nonlocal_node)
		names = [children[i].value for i in range(1, len(children), 2)]
		return ast.Nonlocal(names, nonlocal_node)


	def handle_assert_stmt(self, assert_node):
		children = self.children(assert_node)
		child_count = len(children)
		expr = self.handle_expr(children[1])
		msg = None
		if len(children) == 4:
			msg = self.handle_expr(children[3])
		return ast.Assert(expr, msg, assert_node)


	def handle_suite(self, suite_node):
		'''suite: simple_stmt | NEWLINE INDENT stmt+ DEDENT'''
		children = self.children(suite_node)
		first_child = children[0]
		# e.x. -> stuff ':' simple_stmt
		#	otherwise, we get an INDENT [stuff] DEDENT pattern
		if first_child.type == self.syms.simple_stmt:
			return self.handle_simple_stmt(first_child)
		else:
			assert children[0].type == self.tokens.INDENT
			assert children[-1].type == self.tokens.DEDENT
			children = children[1:-1]
			stmts = []
			for stmt in children:
				if stmt.type in self.SKIPTOKENS:
					continue
				assert stmt.type == self.syms.stmt
				stmts.extend(self.handle_stmt(stmt))
		return stmts


	def handle_simple_stmt(self, simple_stmt) -> list:
		'''simple_stmt: small_stmt (';' small_stmt)* [';'] NEWLINE'''
		assert simple_stmt.type == self.syms.simple_stmt
		stmts = []
		children = self.children(simple_stmt)
		for child in children:
			if child.type == self.tokens.SEMI:
				continue
			stmts.append(self.handle_small_stmt(child))
		return stmts


	def handle_stmt(self, stmt) -> list:
		'''Dispatch to a more specific handler.
			Handles exactly one stmt, so this should not be called on stmt
			or simple_stmt unless it is known to hav exactly one stmt in it.
			
			stmt: simple_stmt | compound_stmt
		'''
		assert stmt.type == self.syms.stmt
		children = self.children(stmt)
		assert len(children) == 1
		if children[0].type == self.syms.simple_stmt:
			return self.handle_simple_stmt(children[0])
		elif children[0].type == self.syms.compound_stmt:
			return [self.handle_compound_stmt(children[0])]
		else:
			raise AssertionError('Unrecognized stmt: {}'.format(
					self.type_name(children[0].type)))


	def handle_small_stmt(self, small_stmt):
		'''small_stmt: (expr_stmt | del_stmt | pass_stmt | flow_stmt |
					import_stmt | global_stmt | nonlocal_stmt | assert_stmt)'''
		assert small_stmt.type == self.syms.small_stmt
		children = self.children(small_stmt)
		assert len(children) == 1
		stmt = children[0]
		stmt_type = stmt.type
		if stmt_type == self.syms.expr_stmt:
			return self.handle_expr_stmt(stmt)
		elif stmt_type == self.syms.del_stmt:
			return self.handle_del_stmt(stmt)
		elif stmt_type == self.syms.pass_stmt:
			return ast.Pass(stmt)
		elif stmt_type == self.syms.flow_stmt:
			return self.handle_flow_stmt(stmt)
		elif stmt_type == self.syms.import_stmt:
			return self.handle_import_stmt(stmt)
		elif stmt_type == self.syms.global_stmt:
			return self.handle_global_stmt(stmt)
		elif stmt_type == self.syms.nonlocal_stmt:
			return self.handle_nonlocal_stmt(stmt)
		elif stmt_type == self.syms.assert_stmt:
			return self.handle_assert_stmt(stmt)
		else:
			raise AssertionError("unhandled small statement")


	def handle_compound_stmt(self, compound_stmt):
		'''compound_stmt: if_stmt | while_stmt | for_stmt | try_stmt | 
			with_stmt | funcdef | classdef | decorated'''
		assert compound_stmt.type == self.syms.compound_stmt
		children = self.children(compound_stmt)
		assert len(children) == 1
		stmt = children[0]
		stmt_type = stmt.type
		if stmt_type == self.syms.if_stmt:
			return self.handle_if_stmt(stmt)
		elif stmt_type == self.syms.while_stmt:
			return self.handle_while_stmt(stmt)
		elif stmt_type == self.syms.for_stmt:
			return self.handle_for_stmt(stmt)
		elif stmt_type == self.syms.try_stmt:
			return self.handle_try_stmt(stmt)
		elif stmt_type == self.syms.with_stmt:
			return self.handle_with_stmt(stmt)
		elif stmt_type == self.syms.funcdef:
			return self.handle_funcdef(stmt)
		elif stmt_type == self.syms.classdef:
			return self.handle_classdef(stmt)
		elif stmt_type == self.syms.decorated:
			return self.handle_decorated(stmt)
		else:
			raise AssertionError("unhandled compound statement")


	def handle_if_stmt(self, if_node):
		children = self.children(if_node)
		child_count = len(children)
		if child_count == 4:
			test = self.handle_expr(children[1])
			suite = self.handle_suite(children[3])
			return ast.If(test, suite, None, if_node)
		otherwise_string = children[4].value
		if otherwise_string == "else":
			test = self.handle_expr(children[1])
			suite = self.handle_suite(children[3])
			else_suite = self.handle_suite(children[6])
			return ast.If(test, suite, else_suite, if_node)
		elif otherwise_string == "elif":
			elif_count = child_count - 4
			after_elif = children[elif_count + 1]
			if after_elif.type == self.tokens.NAME and \
					after_elif.value == "else":
				has_else = True
				elif_count -= 3
			else:
				has_else = False
			elif_count //= 4
			if has_else:
				last_elif = children[-6]
				last_elif_test = self.handle_expr(last_elif)
				elif_body = self.handle_suite(children[-4])
				else_body = self.handle_suite(children[-1])
				otherwise = [ast.If(last_elif_test, elif_body, else_body, last_elif)]
				elif_count -= 1
			else:
				otherwise = None
			for i in range(elif_count):
				offset = 5 + (elif_count - i - 1) * 4
				elif_test_node = children[offset]
				elif_test = self.handle_expr(elif_test_node)
				elif_body = self.handle_suite(children[offset + 2])
				new_if = ast.If(elif_test, elif_body, otherwise, elif_test_node)
				otherwise = [new_if]
			expr = self.handle_expr(children[1])
			body = self.handle_suite(children[3])
			return ast.If(expr, body, otherwise, if_node)
		else:
			raise AssertionError("unknown if statement configuration")


	def handle_while_stmt(self, while_node):
		children = self.children(while_node)
		loop_test = self.handle_expr(children[1])
		body = self.handle_suite(children[3])
		if len(children) == 7:
			otherwise = self.handle_suite(children[6])
		else:
			otherwise = None
		return ast.While(loop_test, body, otherwise, while_node)


	def handle_for_stmt(self, for_node):
		children = self.children(for_node)
		target_node = children[1]
		target = self.handle_exprlist(target_node, ast.Store)
		target.set_context(ast.Store)
		expr = self.handle_testlist(children[3])
		body = self.handle_suite(children[5])
		if len(children) == 9:
			otherwise = self.handle_suite(children[8])
		else:
			otherwise = None
		return ast.For(target, expr, body, otherwise, for_node)


	def handle_except_clause(self, exc, body):
		'''except_clause: 'except' [test ['as' NAME]]'''
		test = None
		name = None
		suite = self.handle_suite(body)
		children = self.children(exc)
		child_count = len(children)
		if child_count >= 2:
			test = self.handle_expr(children[1])
		if child_count == 4:
			target = children[3]
			assert children[2].type == self.tokens.NAME and children[2].value == 'as'
			assert target.type == self.tokens.NAME
			name = ast.Name(target.value, ast.Store, target)
		return ast.excepthandler(test, name, suite, exc)


	def handle_try_stmt(self, try_node):
		children = self.children(try_node)
		body = self.handle_suite(children[2])
		child_count = len(children)
		except_count = (child_count - 3) // 3
		otherwise = None
		finally_suite = None
		possible_extra_clause = children[-3]
		if possible_extra_clause.type == self.tokens.NAME:
			if possible_extra_clause.value == "finally":
				if child_count >= 9 and \
						children[-6].type == self.tokens.NAME:
					otherwise = self.handle_suite(children[-4])
					except_count -= 1
				finally_suite = self.handle_suite(children[-1])
				except_count -= 1
			else:
				otherwise = self.handle_suite(children[-1])
				except_count -= 1
		if except_count:
			handlers = []
			for i in range(except_count):
				base_offset = i * 3
				exc = children[3 + base_offset]
				except_body = children[5 + base_offset]
				handlers.append(self.handle_except_clause(exc, except_body))
			except_ast = ast.TryExcept(body, handlers, otherwise, try_node)
			if finally_suite is None:
				return except_ast
			body = [except_ast]
		return ast.TryFinally(body, finally_suite, try_node)


	def handle_with_stmt(self, with_node):
		children = self.children(with_node)
		assert children[0].type == self.tokens.NAME
		assert children[0].value == 'with'
		context_suite = self.handle_suite(children[-1])
		with_items = [children[i] for i in range(1, len(children) - 2, 2)]
		assert len(with_items) > 0
		for with_item in reversed(with_items):
			context_expr, optional_vars = self.handle_with_item(with_item)
			context_suite = ast.With(context_expr, optional_vars, context_suite, with_node)
		return context_suite


	def handle_with_item(self, with_item):
		children = self.children(with_item)
		context_expr = self.handle_testlist(children[0])
		optional_vars = None
		if len(children) > 1:
			assert children[1].type == self.tokens.NAME
			assert children[1].value == 'as'
			optional_vars = self.handle_expr(children[2])
			self.set_context(optional_vars, ast.Store)
		return context_expr, optional_vars


	def handle_classdef(self, classdef_node, decorators=None):
		children = self.children(classdef_node)
		name_node = ast.Name(children[1].value, ast.Store, children[1])
		# e.x. class foo:
		if len(children) == 4:
			body = self.handle_suite(children[3])
			return ast.ClassDef(name_node, None, None, None, None, body, decorators, classdef_node)
		# e.x. class foo():
		if children[3].type == self.tokens.RPAR:
			body = self.handle_suite(children[5])
			return ast.ClassDef(name_node, None, None, None, None, body, decorators, classdef_node)
		# everything else
		bases, keywords, starargs, kwargs = self.handle_arglist(children[3])
		body = self.handle_suite(children[6])
		return ast.ClassDef(name_node, bases, keywords, starargs, kwargs, body, decorators, classdef_node)


	def handle_arglist(self, arglist_node):
		children = self.children(arglist_node)
		starargs = None
		kwargs = None
		keywords = []
		bases = []
		i = 0
		while i < len(children):
			arg = children[i]
			if arg.type == self.tokens.COMMA:
				i += 1
			elif arg.type == self.tokens.RPAR:
				i += 1
			elif arg.type == self.tokens.STAR:
				starargs = self.handle_testlist(children[i + 1])
				i += 2
			elif arg.type == self.tokens.DOUBLESTAR:
				kwargs = self.handle_testlist(children[i + 1])
				i += 2
			elif arg.type == self.syms.argument:
				base = self.handle_argument(arg)
				if isinstance(base, ast.keyword):
					keywords.append(base)
				else:
					bases.append(base)
				i += 1
			else:
				raise Exception("Unknown sym in arglist:", self.type_name(arg))
		return bases, keywords, starargs, kwargs


	def handle_argument(self, argument_node):
		'''argument: test [comp_for] | test '=' test  # Really [keyword '='] test'''
		children = self.children(argument_node)
		if len(children) == 1:
			return self.handle_testlist(children[0])
		elif children[1].type == self.tokens.NAME and children[1].value == 'for':
			return self.handle_genexp(argument_node)
		elif children[1].type == self.tokens.EQUAL:
			key = self.handle_testlist(children[0])
			value = self.handle_testlist(children[2])
			return ast.keyword(key, value, argument_node)


	def handle_decorated(self, decorated_node):
		decos = self.handle_decorators(decorated_node.children[0])
		if decorated_node.children[1].children[0].value == 'def':
			defined = self.handle_funcdef(decorated_node.children[1], decos)
		else:
			defined = self.handle_classdef(decorated_node.children[1], decos)
		return defined


	def handle_funcdef(self, funcdef_node, decorators=None):
		children = self.children(funcdef_node)
		assert children[0].value == 'def'
		assert children[1].type == self.tokens.NAME
		assert children[2].type == self.syms.parameters

		name_node = children[1]
		name = ast.Name(name_node.value, ast.Store, name_node)
		#self.check_forbidden_name(name, name_node)

		args = self.handle_parameters(children[2])
		at = 3
		returns = None
		if children[3].type == self.tokens.RARROW:
			returns = self.handle_expr(children[4])
			at = 5
		assert children[at].type == self.tokens.COLON
		body = self.handle_suite(children[at + 1])

		return ast.FunctionDef(name, args, body, decorators, returns, funcdef_node)


	def handle_decorators(self, decorators_node):
		children = self.children(decorators_node)
		return [self.handle_decorator(dec) for dec in children]


	def handle_decorator(self, decorator_node):
		children = self.children(decorator_node)
		dec_name = self.handle_dotted_name(children[1])
		if len(children) == 2:
			dec = dec_name
		elif len(children) == 4:
			assert children[2].type == self.tokens.LPAR
			assert children[3].type == self.tokens.RPAR
			dec = ast.Call(dec_name, None, None, None, None, decorator_node)
		else:
			assert children[2].type == self.tokens.LPAR
			assert children[-1].type == self.tokens.RPAR
			args, keywords, starargs, kwargs = self.handle_arglist(children[3])
			dec = ast.Call(dec_name, args, keywords, starargs, kwargs, decorator_node)
		return dec


	def handle_dotted_name(self, dotted_name_node):
		base_value = dotted_name_node.children[0].value
		name = ast.Name(base_value, ast.Load, dotted_name_node)
		for i in range(2, len(dotted_name_node.children), 2):
			attr = ast.Name(dotted_name_node.children[i].value, ast.Load, dotted_name_node.children[i])
			name = ast.Attribute(name, attr, ast.Load, dotted_name_node)
		return name


	def handle_parameters(self, arguments_node):
		assert arguments_node.type == self.syms.parameters
		children = self.children(arguments_node)

		# the trivial (and common) case of '()'
		if len(children) == 2:
			assert children[0].type == self.tokens.LPAR
			assert children[1].type == self.tokens.RPAR
			return ast.arguments(None, None, None, None,
				None, None, None, None, arguments_node)

		# hand off to typedargs processing
		args = self.handle_argslist(children[1])
		return args


	def handle_argslist(self, argslist_node):
		'''Both typedargslist and varargslist'''
		assert argslist_node.type == self.syms.typedargslist or \
				argslist_node.type == self.syms.varargslist
		children = self.children(argslist_node)
		i = 0
		child_count = len(children)
		args = []
		defaults = []
		vararg_name = None
		vararg_annotation = None
		kwonlyargs = []
		kw_defaults = []
		kwarg_name = None
		kwarg_annotation = None
		have_args = False
		while i < child_count:
			argument = children[i]
			arg_type = argument.type
			if arg_type == self.syms.tfpdef or arg_type == self.syms.vfpdef:
				if arg_type == self.syms.tfpdef:
					arg = self.handle_tfpdef(argument)
				else:
					arg_name = ast.Name(argument.children[0].value, ast.Param, argument.children[0])
					arg = ast.arg(arg_name, None, argument)
				i += 1
				default = None
				if i < len(children) and children[i].type == self.tokens.EQUAL:
					i += 1
					default = self.handle_testlist(children[i])
					i += 1
				if not have_args:
					args.append(arg)
					if default:
						defaults.append(default)
				else:
					kwonlyargs.append(arg)
					kw_defaults.append(default)
			#elif arg_type == self.syms.vfpdef:
			#	assert argument.children[0].type == self.tokens.NAME
			#	args.append(ast.arg(argument.children[0].value, None, argument))
			#	i += 1
			elif arg_type == self.tokens.COMMA:
				i += 1
			elif arg_type == self.tokens.STAR:
				if len(children) >= i and children[i + 1].type == self.syms.tfpdef:
					vararg = self.handle_tfpdef(children[i + 1])
					vararg_name = vararg.arg
					vararg_annotation = vararg.annotation
					i += 3
				elif len(children) >= i and children[i + 1].type == self.syms.vfpdef:
					vararg = self.handle_vfpdef(children[i + 1])
					vararg_name = vararg.arg
					i += 3
				else:
					i += 2
				have_args = True
			elif arg_type == self.tokens.DOUBLESTAR:
				if len(children) >= i and children[i + 1].type == self.syms.tfpdef:
					kwarg = self.handle_tfpdef(children[i + 1])
					kwarg_name = kwarg.arg
					kwarg_annotation = kwarg.annotation
					i += 3
				elif len(children) >= i and children[i + 1].type == self.syms.vfpdef:
					kwarg = self.handle_vfpdef(children[i + 1])
					kwarg_name = kwarg.arg
					i += 3
			else:
				raise NotImplementedError("In argslist type: {}".format(self.type_name(arg_type)))
		return ast.arguments(
					args, vararg_name, vararg_annotation,
					kwonlyargs, kwarg_name, kwarg_annotation,
					defaults, kw_defaults,
					argslist_node)


	def handle_tfpdef(self, tfpdef_node):
		'''tfpdef: NAME [':' test]'''
		assert tfpdef_node.type == self.syms.tfpdef
		children = self.children(tfpdef_node)
		assert children[0].type == self.tokens.NAME
		name = ast.Name(children[0].value, ast.Param, children[0])
		annotation = None
		if len(children) > 1:
			assert children[1].type == self.tokens.COLON
			annotation = self.handle_testlist(children[2])
		return ast.arg(name, annotation, tfpdef_node)


	def handle_vfpdef(self, vfpdef_node):
		'''tfpdef: NAME'''
		assert vfpdef_node.type == self.syms.vfpdef
		children = self.children(vfpdef_node)
		assert children[0].type == self.tokens.NAME
		name = ast.Name(children[0].value, ast.Param, children[0])
		return ast.arg(name, None, vfpdef_node)


	def handle_expr_stmt(self, stmt):
		children = self.children(stmt)
		if len(children) == 1:
			expression = self.handle_testlist(children[0])
			return ast.Expr(expression, stmt)
		elif children[1].type == self.syms.augassign:
			target_child = children[0]
			target_expr = self.handle_testlist(target_child)
			self.set_context(target_expr, ast.Aug)
			value_child = children[2]
			if value_child.type == self.syms.testlist:
				value_expr = self.handle_testlist(value_child)
			else:
				value_expr = self.handle_expr(value_child)
			op_str = children[1].children[0].value
			operator = self.augassign_operator_map[op_str]
			return ast.AugAssign(target_expr, operator, value_expr, stmt)
		else: # Normal assignment.
			targets = []
			for i in range(0, len(children) - 2, 2):
				target_node = children[i]
				if target_node.type == self.syms.yield_expr:
					self.error("can't assign to yield expression", target_node)
				target_expr = self.handle_testlist(target_node)
				self.set_context(target_expr, ast.Store)
				targets.append(target_expr)
			value_child = children[-1]
			if value_child.type == self.syms.testlist:
				value_expr = self.handle_testlist(value_child)
			else:
				value_expr = self.handle_expr(value_child)
			return ast.Assign(targets, value_expr, stmt)


	def get_expression_list(self, tests):
		children = self.children(tests)
		return [self.handle_expr(children[i])
				for i in range(0, len(children), 2)]


	def handle_testlist(self, tests):
		children = self.children(tests)
		if len(children) == 1:
			return self.handle_expr(children[0])
		else:
			elts = self.get_expression_list(tests)
			return ast.Tuple(elts, ast.Load, tests)


	def handle_expr(self, expr_node):
		# Loop until we return something.
		while True:
			children = self.children(expr_node)
			expr_node_type = expr_node.type
			if expr_node_type in (self.syms.test, self.syms.test_nocond):
				first_child = children[0]
				if first_child.type in (self.syms.lambdef, self.syms.lambdef_nocond):
					return self.handle_lambdef(first_child)
				elif len(children) > 1:
					return self.handle_ifexp(expr_node)
				else:
					expr_node = first_child
			elif expr_node_type == self.syms.testlist_star_expr:
				return self.handle_expr(children[0])
			elif expr_node_type == self.syms.or_test or \
					expr_node_type == self.syms.and_test:
				if len(children) == 1:
					expr_node = children[0]
					continue
				seq = [self.handle_expr(children[i])
					   for i in range(0, len(children), 2)]
				if expr_node_type == self.syms.or_test:
					op = ast.Or
				else:
					op = ast.And
				return ast.BoolOp(op, seq, expr_node)
			elif expr_node_type == self.syms.not_test:
				if len(children) == 1:
					expr_node = children[0]
					continue
				expr = self.handle_expr(children[1])
				return ast.UnaryOp(ast.Not, expr, expr_node)
			elif expr_node_type == self.syms.comparison:
				if len(children) == 1:
					expr_node = children[0]
					continue
				operators = []
				operands = []
				expr = self.handle_expr(children[0])
				for i in range(1, len(children), 2):
					operators.append(self.handle_comp_op(children[i]))
					operands.append(self.handle_expr(children[i + 1]))
				return ast.Compare(expr, operators, operands, expr_node)
			elif expr_node_type == self.syms.expr or \
					expr_node_type == self.syms.xor_expr or \
					expr_node_type == self.syms.and_expr or \
					expr_node_type == self.syms.shift_expr or \
					expr_node_type == self.syms.arith_expr or \
					expr_node_type == self.syms.term:
				if len(children) == 1:
					expr_node = children[0]
					continue
				return self.handle_binop(expr_node)
			elif expr_node_type == self.syms.yield_expr:
				if len(children) == 2:
					exp = self.handle_testlist(children[1])
				else:
					exp = None
				return ast.Yield(exp, expr_node)
			elif expr_node_type == self.syms.factor:
				if len(children) == 1:
					expr_node = children[0]
					continue
				return self.handle_factor(expr_node)
			elif expr_node_type == self.syms.power:
				return self.handle_power(expr_node)
			elif expr_node_type == self.syms.lambdef:
				return self.handle_lambdef(expr_node)
			elif expr_node_type == self.syms.star_expr:
				assert len(children) == 2
				assert children[0].type == self.tokens.STAR
				assert children[0].value == '*'
				value = self.handle_expr(children[1])
				return ast.Starred(value, ast.Load, expr_node)
			else:
				raise AssertionError("unknown expr: {}".format(
					self.type_name(expr_node_type)))


	def handle_lambdef(self, lambdef_node):
		children = self.children(lambdef_node)
		assert children[0].type == self.tokens.NAME and children[0].value == 'lambda'
		expr = self.handle_expr(children[-1])
		if len(children) == 3:
			assert children[1].type == self.tokens.COLON and children[1].value == ':'
			args = ast.arguments(None, None, None, None, None, None, None, None, lambdef_node)
		else:
			args = self.handle_varargslist(children[1])
		return ast.Lambda(args, [ast.Return(expr, children[-1])], lambdef_node)


	def handle_varargslist(self, varargslist_node):
		return self.handle_argslist(varargslist_node)


	def handle_ifexp(self, if_expr_node):
		body = self.handle_expr(if_expr_node.children[0])
		expression = self.handle_expr(if_expr_node.children[2])
		otherwise = self.handle_expr(if_expr_node.children[4])
		return ast.IfExp(expression, body, otherwise, if_expr_node)


	def handle_comp_op(self, comp_op_node):
		comp_node = comp_op_node.children[0]
		comp_type = comp_node.type
		if len(comp_op_node.children) == 1:
			if comp_type == self.tokens.LESS:
				return ast.Lt
			elif comp_type == self.tokens.GREATER:
				return ast.Gt
			elif comp_type == self.tokens.EQEQUAL:
				return ast.Eq
			elif comp_type == self.tokens.LESSEQUAL:
				return ast.LtE
			elif comp_type == self.tokens.GREATEREQUAL:
				return ast.GtE
			elif comp_type == self.tokens.NOTEQUAL:
				return ast.NotEq
			elif comp_type == self.tokens.NAME:
				if comp_node.value == "is":
					return ast.Is
				elif comp_node.value == "in":
					return ast.In
				else:
					raise AssertionError("invalid comparison")
			else:
				raise AssertionError("invalid comparison")
		else:
			if comp_op_node.children[1].value == "in":
				return ast.NotIn
			elif comp_node.value == "is":
				return ast.IsNot
			else:
				raise AssertionError("invalid comparison")


	def handle_binop(self, binop_node):
		children = self.children(binop_node)
		left = self.handle_expr(children[0])
		right = self.handle_expr(children[2])
		op = self.operator_map[children[1].type]
		result = ast.BinOp(left, op, right, binop_node)
		number_of_ops = (len(children) - 1) // 2
		for i in range(1, number_of_ops):
			op_node = children[i * 2 + 1]
			op = self.operator_map[op_node.type]
			sub_right = self.handle_expr(children[i * 2 + 2])
			result = ast.BinOp(result, op, sub_right, op_node)
		return result


	def handle_factor(self, factor_node):
		# Fold '-' on constant numbers.
		if factor_node.children[0].type == self.tokens.MINUS and \
				len(factor_node.children) == 2:
			factor = factor_node.children[1]
			if factor.type == self.syms.factor and len(factor.children) == 1:
				power = factor.children[0]
				if power.type == self.syms.power and len(power.children) == 1:
					atom = power.children[0]
					if atom.type == self.syms.atom and \
							atom.children[0].type == self.tokens.NUMBER:
						num = atom.children[0]
						num.value = "-" + num.value
						return self.handle_atom(atom)
		expr = self.handle_expr(factor_node.children[1])
		op_type = factor_node.children[0].type
		if op_type == self.tokens.PLUS:
			op = ast.UAdd
		elif op_type == self.tokens.MINUS:
			op = ast.USub
		elif op_type == self.tokens.TILDE:
			op = ast.Invert
		else:
			raise AssertionError("invalid factor node")
		return ast.UnaryOp(op, expr, factor_node)


	def handle_power(self, power_node):
		children = self.children(power_node)
		atom_expr = self.handle_atom(children[0])
		if len(children) == 1:
			return atom_expr
		for i in range(1, len(children)):
			trailer = children[i]
			if trailer.type != self.syms.trailer:
				break
			tmp_atom_expr = self.handle_trailer(trailer, atom_expr)
			tmp_atom_expr.llcopy(atom_expr)
			atom_expr = tmp_atom_expr
		if children[-1].type == self.syms.factor:
			right = self.handle_expr(children[-1])
			atom_expr = ast.BinOp(atom_expr, ast.Pow, right, power_node)
		return atom_expr


	def handle_slice(self, slice_node):
		children = self.children(slice_node)
		first_child = children[0]
		if first_child.type == self.tokens.DOT:
			return ast.Ellipsis(slice_node)
		if len(children) == 1 and first_child.type == self.syms.test:
			index = self.handle_expr(first_child)
			return ast.Index(index, slice_node)
		lower = None
		upper = None
		step = None
		if first_child.type == self.syms.test:
			lower = self.handle_expr(first_child)
		if first_child.type == self.tokens.COLON:
			if len(children) > 1:
				second_child = children[1]
				if second_child.type == self.syms.test:
					upper = self.handle_expr(second_child)
		elif len(children) > 2:
			third_child = children[2]
			if third_child.type == self.syms.test:
				upper = self.handle_expr(third_child)
		last_child = children[-1]
		if last_child.type == self.syms.sliceop:
			if len(last_child.children) == 1:
				step = ast.Name("None", ast.Load, last_child)
			else:
				step_child = last_child.children[1]
				if step_child.type == self.syms.test:
					step = self.handle_expr(step_child)
		return ast.Slice(lower, upper, step, slice_node)


	def handle_trailer(self, trailer_node, left_expr):
		children = self.children(trailer_node)
		first_child = children[0]
		if first_child.type == self.tokens.LPAR:
			if len(children) == 2:
				return ast.Call(left_expr, None, None, None, None, trailer_node)
			else:
				bases, keywords, starargs, kwargs = self.handle_arglist(children[1])
				return ast.Call(left_expr, bases, keywords, starargs, kwargs, trailer_node)
		elif first_child.type == self.tokens.DOT:
			attr = ast.Name(children[1].value, ast.Load, children[1])
			return ast.Attribute(left_expr, attr, ast.Load, trailer_node)
		else:
			middle = children[1]
			if len(middle.children) == 1:
				slice = self.handle_slice(middle.children[0])
				return ast.Subscript(left_expr, slice, ast.Load, middle)
			slices = []
			simple = True
			for i in range(0, len(middle.children), 2):
				slc = self.handle_slice(middle.children[i])
				if not isinstance(slc, ast.Index):
					simple = False
				slices.append(slc)
			if not simple:
				ext_slice = ast.ExtSlice(slices)
				return ast.Subscript(left_expr, ext_slice, ast.Load, middle)
			elts = []
			for idx in slices:
				assert isinstance(idx, ast.Index)
				elts.append(idx.value)
			tup = ast.Tuple(elts, ast.Load, middle)
			return ast.Subscript(left_expr, ast.Index(tup, middle), ast.Load, middle)


	def parse_number(self, raw):
		try:
			return int(raw)
		except ValueError:
			if raw.startswith('0x'):
				return int(raw[2:], 16)
			elif raw.startswith('0o'):
				return int(raw[2:], 8)
			elif raw.startswith('0b'):
				return int(raw[2:], 2)
			else:
				return float(raw)
		raise AssertionError("Invalid literal number type: {}".format(raw))


	#FIXME: this can sometimes be a Store op, e.g. as optional_vars on with_stmt
	def handle_atom(self, atom_node):
		children = self.children(atom_node)
		first_child = children[0]
		first_child_type = first_child.type
		if first_child_type == self.tokens.NAME:
			return ast.Name(first_child.value, ast.Load, first_child)
		elif first_child_type == self.tokens.STRING:
			sub_strings = [s.value for s in children]
			if len(sub_strings) > 0:
				final_string = ''.join(sub_strings)
			else:
				final_string = sub_strings
			return ast.Str(final_string, atom_node)
		elif first_child_type == self.tokens.NUMBER:
			num_value = self.parse_number(first_child.value)
			return ast.Num(num_value, atom_node)
		elif first_child_type == self.tokens.ELLIPSIS:
			return ast.Ellipsis(atom_node)
		elif first_child_type == self.tokens.LPAR:
			second_child = children[1]
			if second_child.type == self.tokens.RPAR:
				return ast.Tuple(None, ast.Load, atom_node)
			elif second_child.type == self.syms.yield_expr:
				return self.handle_expr(second_child)
			return self.handle_testlist_gexp(second_child)
		elif first_child_type == self.tokens.LSQB:
			second_child = children[1]
			if second_child.type == self.tokens.RSQB:
				return ast.List(None, ast.Load, atom_node)
			second_children = self.children(second_child)
			if len(second_children) == 1 or \
					second_children[1].type == self.tokens.COMMA:
				elts = self.get_expression_list(second_child)
				return ast.List(elts, ast.Load, atom_node)
			return self.handle_listcomp(second_child)
		elif first_child_type == self.tokens.LBRACE:
			second_child = children[1]
			if second_child.type == self.tokens.RBRACE:
				return ast.Dict(None, None, atom_node)
			return self.handle_dictorsetmaker(second_child, atom_node)
		else:
			raise AssertionError("unknown atom")


	#dictorsetmaker: ( (test ':' test (comp_for | (',' test ':' test)* [','])) |
	#              (test (comp_for | (',' test)* [','])) )
	def handle_dictorsetmaker(self, second_child, atom_node):
		children = self.children(second_child)
		# SET
		if len(children) < 2 or children[1].type != self.tokens.COLON:
			# Set Comprehension
			if len(children) == 2 and children[1].type == self.syms.comp_for:
				elt = self.handle_testlist(children[0])
				comps = self.handle_comp_for(children[1])
				elt.set_context(ast.Load)
				return ast.SetComp(elt, comps, atom_node)
			# Normal Set
			else:
				values = []
				for i in range(0, len(children), 2):
					values.append(self.handle_testlist(children[i]))
				return ast.Set(values, atom_node)
		# DICT
		else:
			# Dict Comprehension
			# test ':' test comp_for
			if len(children) == 4 and children[3].type == self.syms.comp_for:
				key = self.handle_testlist(children[0])
				value = self.handle_testlist(children[2])
				generators = self.handle_comp_for(children[3])
				key.set_context(ast.Store)
				value.set_context(ast.Store)
				return ast.DictComp(key, value, generators, atom_node)
			# Normal Dict
			else:
				keys = []
				values = []
				for i in range(0, len(children), 4):
					keys.append(self.handle_testlist(children[i]))
					values.append(self.handle_testlist(children[i + 2]))
				return ast.Dict(keys, values, atom_node)


	def handle_comp_for(self, comp_for_node) -> [ast.comprehension]:
		'''comp_for: 'for' exprlist 'in' or_test [comp_iter]'''
		comps = []
		children = self.children(comp_for_node)
		target = self.handle_exprlist(children[1], ast.Store)
		iter_ = self.handle_testlist(children[3])
		ifs = []
		if len(children) > 4:
			iter_children = self.children(children[4])
			if iter_children[0].type == self.syms.comp_for:
				return [ast.comprehension(target, iter_, [], comp_for_node)] + \
						self.handle_comp_for(iter_children[0])
			else:
				assert iter_children[0].type == self.syms.comp_if
				ifs, comps = self.handle_comp_if(iter_children[0])
				return [ast.comprehension(target, iter_, ifs, comp_for_node)] + comps
		return [ast.comprehension(target, iter_, [], comp_for_node)]


	def handle_comp_if(self, comp_iter_node) -> ([ast.expr], [ast.comprehension]):
		'''comp_if: 'if' test_nocond [comp_iter]'''
		children = self.children(comp_iter_node)
		ifs = [self.handle_testlist(children[1])]
		comps = []
		if len(children) > 2:
			iter_children = self.children(children[2])
			if iter_children[0].type == self.syms.comp_for:
				comps = self.handle_comp_for(iter_children[0])
			else:
				assert iter_children[0].type == self.syms.comp_if
				extra_ifs, comps = self.handle_comp_if(iter_children[0])
				ifs.extend(extra_ifs)
		return ifs, comps


	def handle_testlist_gexp(self, gexp_node):
		if len(gexp_node.children) > 1 and \
				gexp_node.children[1].type == self.syms.comp_for:
			return self.handle_genexp(gexp_node)
		return self.handle_testlist(gexp_node)


	def count_comp_fors(self, comp_node, for_type, if_type):
		count = 0
		current_for = self.children(comp_node)[1]
		while True:
			count += 1
			if len(self.children(current_for)) == 5:
				current_iter = self.children(current_for)[4]
			else:
				return count
			while True:
				first_child = self.children(current_iter)[0]
				if first_child.type == for_type:
					current_for = self.children(current_iter)[0]
					break
				elif first_child.type == if_type:
					if len(self.children(first_child)) == 3:
						current_iter = self.children(first_child)[2]
					else:
						return count
				else:
					raise AssertionError("should not reach here")


	def count_comp_ifs(self, iter_node, for_type):
		count = 0
		while True:
			first_child = iter_node.children[0]
			if first_child.type == for_type:
				return count
			count += 1
			if len(first_child.children) == 2:
				return count
			iter_node = first_child.children[2]


	def comprehension_helper(self, comp_node, for_type, if_type, iter_type,
							 handle_source_expression):
		elt = self.handle_expr(comp_node.children[0])
		elt.set_context(ast.Load)
		fors_count = self.count_comp_fors(comp_node, for_type, if_type)
		comps = []
		comp_for = self.children(comp_node)[1]
		for i in range(fors_count):
			for_node = self.children(comp_for)[1]
			for_targets = self.handle_exprlist(for_node, ast.Store)
			expr = handle_source_expression(self.children(comp_for)[3])
			assert isinstance(expr, ast.expr)
			if len(self.children(for_node)) == 1:
				comp = ast.comprehension(for_targets, expr, None, comp_for)
			else:
				comp = ast.comprehension(for_targets, expr, None, comp_node)
			if len(self.children(comp_for)) == 5:
				comp_for = comp_iter = self.children(comp_for)[4]
				assert comp_iter.type == iter_type
				ifs_count = self.count_comp_ifs(comp_iter, for_type)
				if ifs_count:
					ifs = []
					for j in range(ifs_count):
						comp_for = comp_if = self.children(comp_iter)[0]
						ifs.append(self.handle_expr(self.children(comp_if)[1]))
						if len(self.children(comp_if)) == 3:
							comp_for = comp_iter = self.children(comp_if)[2]
					comp.ifs = ifs
				if comp_for.type == iter_type:
					comp_for = self.children(comp_for)[0]
			assert isinstance(comp, ast.comprehension)
			comps.append(comp)
		return elt, comps


	def handle_genexp(self, genexp_node):
		elt, comps = self.comprehension_helper(genexp_node, self.syms.comp_for,
											   self.syms.comp_if, self.syms.comp_iter,
											   self.handle_expr)
		return ast.GeneratorExp(elt, comps, genexp_node)


	def handle_listcomp(self, listcomp_node):
		elt, comps = self.comprehension_helper(listcomp_node, self.syms.comp_for,
											   self.syms.comp_if, self.syms.comp_iter,
											   self.handle_testlist)
		return ast.ListComp(elt, comps, listcomp_node)


	def handle_exprlist(self, exprlist, context):
		exprs = []
		children = self.children(exprlist)
		for i in range(0, len(children), 2): # skip commas
			child = children[i]
			expr = self.handle_expr(child)
			self.set_context(expr, context)
			exprs.append(expr)
		if len(exprs) == 1:
			return exprs[0]
		return ast.Tuple(exprs, context, exprlist)


