'''
Convert the low-level parse tree into a high-level Abstract Syntax Tree.

NOTES for Melano:
	- Copied and adapted from pypy; this involved a complete rewrite of many
		different elements to support new python3 constructs.
	- Passes the low-level Node to the ast nodes directly, rather than pulling
		off and passing start line and column individually.
	- Handles our skiptokens by filtering the children lists as needed.
'''
import melano.parser.py3.ast as ast
from pprint import pprint



class PythonASTBuilder:
	'''Convert the low-level ast produced by parsing into a high-level ast
		useful for scanning, linting, etc.'''
	def __init__(self, parser):
		self.parser = parser

		class _Symbols: pass
		self.syms = _Symbols()
		for index, name in self.parser.grammar.symbol_names.items():
			setattr(self.syms, name, index)
		# temp py2 compatibility
		setattr(self.syms, 'old_test', 1000)
		setattr(self.syms, 'old_lambdef', 1001)
		setattr(self.syms, 'print_stmt', 1002)
		#print(sorted(dir(self.syms)))

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

		stmts = []
		for stmt in node.children:
			ty = stmt.type
			if ty in self.SKIPTOKENS:
				stmts.append(stmt)
				continue
			sub_stmts_count = self.number_of_statements(stmt)
			if sub_stmts_count == 1:
				stmts.append(self.handle_stmt(stmt))
			else:
				for j in range(sub_stmts_count):
					small_stmt = stmt.children[j * 2]
					stmts.append(self.handle_stmt(small_stmt))

		node.endpos = stmts[-1].endpos
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
				self.pretty_print(c, level+1)


	def number_of_statements(self, stmt):
		"""Compute the number of AST statements contained in a node."""
		ty = stmt.type
		if ty == self.syms.compound_stmt:
			return 1
		elif ty == self.syms.stmt:
			return self.number_of_statements(stmt.children[0])
		elif ty == self.syms.simple_stmt:
			# Divide to remove semi-colons.
			return len(stmt.children) // 2
		else:
			raise AssertionError("non-statement node: {}".format(self.type_name(stmt.type)))


	def set_context(self, expr, ctx):
		"""Set the context of an expression to Store or Del if possible."""
		try:
			expr.set_context(ctx)
		except ast.UnacceptableExpressionContext as e:
			self.error_ast(e.msg, e.node)
		except misc.ForbiddenNameAssignment as e:
			self.error_ast("assignment to %s" % (e.name,), e.node)


	def handle_print_stmt(self, print_node):
		dest = None
		expressions = None
		newline = True
		start = 1
		child_count = len(print_node.children)
		if child_count > 2 and print_node.children[1].type == self.tokens.RIGHTSHIFT:
			dest = self.handle_expr(print_node.children[2])
			start = 4
		if (child_count + 1 - start) // 2:
			expressions = [self.handle_expr(print_node.children[i])
						   for i in range(start, child_count, 2)]
		if print_node.children[-1].type == self.tokens.COMMA:
			newline = False
		return ast.Print(dest, expressions, newline, print_node)


	def handle_del_stmt(self, del_node):
		children = self.children(del_node)
		targets = self.handle_exprlist(children[1], ast.Del)
		return ast.Delete(targets, del_node)


	def handle_flow_stmt(self, flow_node):
		first_child = flow_node.children[0]
		first_child_type = first_child.type
		if first_child_type == self.syms.break_stmt:
			return ast.Break(flow_node)
		elif first_child_type == self.syms.continue_stmt:
			return ast.Continue(flow_node)
		elif first_child_type == self.syms.yield_stmt:
			yield_expr = self.handle_expr(first_child.children[0])
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
			#traceback = None
			child_count = len(first_child.children)
			if child_count >= 2:
				exc = self.handle_expr(first_child.children[1])
			if child_count >= 4:
				value = self.handle_expr(first_child.children[3])
			#if child_count == 6:
			#	traceback = self.handle_expr(first_child.children[5])
			return ast.Raise(exc, value, flow_node)
		else:
			raise AssertionError("unknown flow statement")

	"""
	def alias_for_import_name(self, import_name, store=True):
		#self.print_children(import_name)
		children = self.children(import_name)
		while True:
			import_name_type = import_name.type
			if import_name_type == self.syms.import_as_name:
				name = import_name.children[0].value
				if len(import_name.children) == 3:
					# 'as' is not yet a keyword in Python 2.5, so the grammar
					# just specifies a NAME token.  We check it manually here.
					if import_name.children[1].value != "as":
						self.error("must use 'as' in import", import_name)
					as_name = import_name.children[2].value
					#self.check_forbidden_name(as_name, import_name.children[2])
					return ast.alias(name, as_name)
				else:
					as_name = None
					#self.check_forbidden_name(name, import_name.children[0])
				return ast.alias(name, as_name)
			elif import_name_type == self.syms.dotted_as_name:
				if len(import_name.children) == 1:
					import_name = import_name.children[0]
					continue
				if import_name.children[1].value != "as":
					self.error("must use 'as' in import", import_name)
				alias = self.alias_for_import_name(import_name.children[0])
				asname_node = import_name.children[2]
				alias.asname = asname_node.value
				#self.check_forbidden_name(alias.asname, asname_node)
				return alias
			elif import_name_type == self.syms.dotted_name:
				if len(import_name.children) == 1:
					name = import_name.children[0].value
					#if store:
					#	self.check_forbidden_name(name, import_name.children[0])
					return ast.alias(name, None)
				name_parts = [import_name.children[i].value
							  for i in range(0, len(import_name.children), 2)]
				name = ".".join(name_parts)
				return ast.alias(name, None)
			elif import_name_type == self.tokens.STAR:
				return ast.alias("*", None)
			else:
				raise AssertionError("unknown import name")
	"""

	def handle_import_stmt(self, import_node):
		children = self.children(import_node)
		if children[0].type == self.syms.import_name:
			return self.handle_import_name(children[0])
		elif children[0].type == self.syms.import_from:
			return self.handle_import_from(children[0])
		else:
			raise AssertionError("unknown import node")
		"""
		self.pretty_print(import_node)
		import_node = import_node.children[0]
		children = self.children(import_node)
		if import_node.type == self.syms.import_name:
			dotted_as_names = children[1]
			aliases = [self.alias_for_import_name(dotted_as_names.children[i])
					   for i in range(0, len(dotted_as_names.children), 2)]
			return ast.Import(aliases, import_node)
		elif import_node.type == self.syms.import_from:
			child_count = len(children)
			module = None
			modname = None
			i = 1
			dot_count = 0
			while i < child_count:
				#print(children)
				child = children[i]
				if child.type == self.syms.dotted_name:
					module = self.alias_for_import_name(child, False)
					i += 1
					break
				elif child.type != self.tokens.DOT:
					break
				i += 1
				dot_count += 1
			i += 1
			after_import_type = children[i].type
			star_import = False
			if after_import_type == self.tokens.STAR:
				names_node = children[i]
				star_import = True
			elif after_import_type == self.tokens.LPAR:
				names_node = children[i + 1]
			elif after_import_type == self.syms.import_as_names:
				names_node = children[i]
				if len(names_node.children) % 2 == 0:
					self.error("trailing comma is only allowed with "
							   "surronding parenthesis", names_node)
			else:
				raise AssertionError("unknown import node")
			if star_import:
				aliases = [self.alias_for_import_name(names_node)]
			else:
				aliases = [self.alias_for_import_name(names_node.children[i])
						   for i in range(0, len(names_node.children), 2)]
			if module is not None:
				modname = module.name
			return ast.ImportFrom(modname, aliases, dot_count, import_node)
		else:
			raise AssertionError("unknown import node")
		"""
	
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
			module = ''
		assert children[at].value == 'import'
		at += 1
		if children[at].type == self.syms.import_as_names:
			names = self.handle_import_as_names(children[at])
		elif children[at].type == self.tokens.STAR:
			names = [ast.alias("*", None)]
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
		name = children[0].value
		asname = None
		if len(children) > 1:
			assert children[1].value == 'as'
			assert children[2].type == self.tokens.NAME
			asname = children[2].value
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
			asname = children[2].value
		return ast.alias(name, asname)
	

	def handle_global_stmt(self, global_node):
		children = self.children(global_node)
		names = [children[i].value for i in range(1, len(children), 2)]
		return ast.Global(names, global_node)


	def handle_nonlocal_stmt(self, nonlocal_node):
		children = self.children(nonlocal_node)
		names = [children[i].value for i in range(1, len(children), 2)]
		return ast.NonLocal(names, nonlocal_node)


	def handle_exec_stmt(self, exec_node):
		children = self.children(exec_node)
		child_count = len(children)
		globs = None
		locs = None
		to_execute = self.handle_expr(children[1])
		if child_count >= 4:
			globs = self.handle_expr(children[3])
		if child_count == 6:
			locs = self.handle_expr(children[5])
		return ast.Exec(to_execute, globs, locs, exec_node)

	def handle_assert_stmt(self, assert_node):
		children = self.children(assert_node)
		child_count = len(children)
		expr = self.handle_expr(children[1])
		msg = None
		if len(children) == 4:
			msg = self.handle_expr(children[3])
		return ast.Assert(expr, msg, assert_node)

	def handle_suite(self, suite_node):
		children = self.children(suite_node)
		first_child = children[0]
		if first_child.type == self.syms.simple_stmt:
			end = len(first_child.children) - 1
			if first_child.children[end - 1].type == self.tokens.SEMI:
				end -= 1
			stmts = [self.handle_stmt(first_child.children[i])
					 for i in range(0, end, 2)]
		else:
			stmts = []
			for i in range(2, len(children) - 1):
				stmt = children[i]
				ty = stmt.type
				if ty in self.SKIPTOKENS:
					stmts.append(stmt)
					continue
				stmt_count = self.number_of_statements(stmt)
				if stmt_count == 1:
					stmts.append(self.handle_stmt(stmt))
				else:
					simple_stmt = stmt.children[0]
					for j in range(0, len(simple_stmt.children), 2):
						stmt = simple_stmt.children[j]
						if not stmt.children:
							break
						stmts.append(self.handle_stmt(stmt))
		return stmts

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
		target_as_exprlist = self.handle_exprlist(target_node, ast.Store)
		if len(target_node.children) == 1:
			target = target_as_exprlist[0]
		else:
			target = ast.Tuple(target_as_exprlist, ast.Store, target_node)
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
		target = None
		suite = self.handle_suite(body)
		child_count = len(exc.children)
		if child_count >= 2:
			test = self.handle_expr(exc.children[1])
		if child_count == 4:
			target = exc.children[3]
			assert target.type == self.tokens.NAME
			#target = self.handle_expr(target_child)
			#self.set_context(target, ast.Store)
		return ast.excepthandler(test, target, suite, exc)

	def handle_try_stmt(self, try_node):
		children = self.children(try_node)
		body = self.handle_suite(children[2])
		child_count = len(children)
		except_count = (child_count - 3 ) // 3
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
		return context_expr, optional_vars

		'''
		context_expr = None
		optional_vars = None
		body = None
		if len(children) == 4: # 'with' test ':' suite
			context_expr = self.handle_testlist(children[1])
			body = self.handle_suite(children[3])
		elif len(children) == 6: # 'with' test 'as' expr ':' suite
			context_expr = self.handle_testlist(children[1])
			optional_vars = self.handle_expr(children[3])
			body = self.handle_suite(children[5])
		else: # 'with' test ['as' expr] ',' ... ':' body
			context_expr = self.handle_testlist(children[1])
			if children[2].type == self.tokens.NAME and \
					children[2].value == 'as':
				optional_vars = self.handle_expr(children[3])
				body = self.handle_with_stmt_remainder(children[5:], with_node)
			else:
				optional_vars = None
				body = self.handle_with_stmt_remainder(children[3:], with_node)
		return ast.With(context_expr, optional_vars, body, with_node)
		'''
		'''
	def handle_with_stmt_remainder(self, with_items, with_node):
		if len(with_items) == 2: # last item in list
			assert with_items[0].type == self.tokens.COLON
			return self.handle_suite(with_items[1])

		context_expr = self.handle_testlist(with_items[0])
		optional_vars = None
		pos = 1
		if with_items[1].type == self.tokens.NAME and \
				with_items[1].value == 'as':
			optional_vars = self.handle_expr(children[3])
			pos += 2
		body = self.handle_with_stmt_remainder(children[pos:])
		return [ast.With(context_expr, optional_var, body, with_node)]
		'''
		'''
		test = self.handle_expr(with_node.children[1])
		if len(with_node.children) == 5:
			target_node = with_node.children[2]
			target = self.handle_with_var(target_node)
			self.set_context(target, ast.Store)
		else:
			target = None
		return ast.With(test, target, body, with_node)
		'''
	'''
	def handle_with_var(self, with_var_node):
		# The grammar doesn't require 'as', so check it manually.
		if with_var_node.children[0].value != "as":
			self.error("expected \"with [expr] as [var]\"", with_var_node)
		return self.handle_expr(with_var_node.children[1])
	'''

	def handle_classdef(self, classdef_node, decorators=None):
		children = self.children(classdef_node)
		name_node = children[1]
		name = name_node.value
		# e.x. class foo:
		if len(children) == 4:
			body = self.handle_suite(children[3])
			return ast.ClassDef(name, None, None, None, None, body, decorators, classdef_node)
		# e.x. class foo():
		if children[3].type == self.tokens.RPAR:
			body = self.handle_suite(children[5])
			return ast.ClassDef(name, None, None, None, None, body, decorators, classdef_node)
		# everything else
		#self.pretty_print(classdef_node)
		bases, keywords, starargs, kwargs = self.handle_arglist(children[3])
		body = self.handle_suite(children[6])
		return ast.ClassDef(name, bases, keywords, starargs, kwargs, body, decorators, classdef_node)


	def handle_arglist(self, arglist_node):
		#self.pretty_print(arglist_node)
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
		name = name_node.value
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
			#dec = self.handle_call(decorator_node.children[3], dec_name)
			#self.pretty_print(decorator_node)
			dec = self.handle_arglist(children[3])
		return dec


	def handle_dotted_name(self, dotted_name_node):
		base_value = dotted_name_node.children[0].value
		name = ast.Name(base_value, ast.Load, dotted_name_node)
		for i in range(2, len(dotted_name_node.children), 2):
			attr = dotted_name_node.children[i].value
			name = ast.Attribute(name, attr, ast.Load, dotted_name_node)
		return name


	def handle_parameters(self, arguments_node):
		'''This should be handle_parameters; Call does not use it.'''
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
		"""		
		i = 0
		child_count = len(children)
		defaults = []
		args = []
		variable_arg = None
		keywords_arg = None
		have_default = False
		while i < child_count:
			argument = children[i]
			arg_type = argument.type
			if arg_type == self.syms.fpdef:
				while True:
					if i + 1 < child_count and \
							children[i + 1].type == self.tokens.EQUAL:
						default_node = children[i + 2]
						defaults.append(self.handle_expr(default_node))
						i += 2
						have_default = True
					elif have_default:
						msg = "non-default argument follows default argument"
						self.error(msg, arguments_node)
					if len(argument.children) == 3:
						sub_arg = argument.children[1]
						if len(sub_arg.children) != 1:
							args.append(self.handle_arg_unpacking(sub_arg))
						else:
							argument = sub_arg.children[0]
							continue
					if argument.children[0].type == self.tokens.NAME:
						name_node = argument.children[0]
						arg_name = name_node.value
						#self.check_forbidden_name(arg_name, name_node)
						name = ast.Name(arg_name, ast.Param, name_node)
						args.append(name)
					i += 2
					break
			elif arg_type == self.tokens.STAR:
				name_node = children[i + 1]
				variable_arg = name_node.value
				#self.check_forbidden_name(variable_arg, name_node)
				i += 3
			elif arg_type == self.tokens.DOUBLESTAR:
				name_node = children[i + 1]
				keywords_arg = name_node.value
				#self.check_forbidden_name(keywords_arg, name_node)
				i += 3
			else:
				raise AssertionError("unknown node in argument list")
		if not defaults:
			defaults = None
		if not args:
			args = None
		return ast.arguments(args, variable_arg, None, keywords_arg, defaults)
		"""

	"""
	def handle_arg_unpacking(self, fplist_node):
		args = []
		for i in range((len(fplist_node.children) + 1) // 2):
			fpdef_node = fplist_node.children[i * 2]
			while True:
				child = fpdef_node.children[0]
				if child.type == self.tokens.NAME:
					arg = ast.Name(child.value, ast.Store, child)
					args.append(arg)
				else:
					child = fpdef_node.children[1]
					if len(child.children) == 1:
						fpdef_node = child.children[0]
						continue
					args.append(self.handle_arg_unpacking(child))
				break
		tup = ast.Tuple(args, ast.Store, fplist_node)
		self.set_context(tup, ast.Store)
		return tup
	"""
	
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
					arg = ast.arg(argument.children[0].value, None, argument)
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
					defaults.append(default)
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
				else:
					i += 2
				have_args = True
			elif arg_type == self.tokens.DOUBLESTAR:
				kwarg = self.handle_tfpdef(children[i + 1])
				kwarg_name = kwarg.arg
				kwarg_annotation = kwarg.annotation
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
		name = children[0].value
		annotation = None
		if len(children) > 1:
			assert children[1].type == self.tokens.COLON
			annotation = self.handle_testlist(children[2])
		return ast.arg(name, annotation, tfpdef_node)


	def handle_stmt(self, stmt):
		'''Dispatch to a more specific handler.'''
		stmt_type = stmt.type
		if stmt_type == self.syms.stmt:
			stmt = stmt.children[0]
			stmt_type = stmt.type
		if stmt_type == self.syms.simple_stmt:
			stmt = stmt.children[0]
			stmt_type = stmt.type
		if stmt_type == self.syms.small_stmt:
			stmt = stmt.children[0]
			stmt_type = stmt.type
			if stmt_type == self.syms.expr_stmt:
				return self.handle_expr_stmt(stmt)
			elif stmt_type == self.syms.print_stmt:
				return self.handle_print_stmt(stmt)
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
			elif stmt_type == self.syms.exec_stmt:
				return self.handle_exec_stmt(stmt)
			else:
				raise AssertionError("unhandled small statement")
		elif stmt_type == self.syms.compound_stmt:
			stmt = stmt.children[0]
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
		else:
			raise AssertionError("unknown statment type")


	def handle_expr_stmt(self, stmt):
		children = self.children(stmt)
		if len(children) == 1:
			expression = self.handle_testlist(children[0])
			return ast.Expr(expression, stmt)
		elif children[1].type == self.syms.augassign:
			target_child = children[0]
			target_expr = self.handle_testlist(target_child)
			self.set_context(target_expr, ast.Store)
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
			if expr_node_type in (self.syms.test, self.syms.old_test, self.syms.test_nocond):
				first_child = children[0]
				if first_child.type in (self.syms.lambdef, self.syms.old_lambdef, self.syms.lambdef_nocond):
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
			else:
				raise AssertionError("unknown expr: {}".format(
					self.type_name(expr_node_type)))


	def handle_lambdef(self, lambdef_node):
		children = self.children(lambdef_node)
		expr = self.handle_expr(children[-1])
		if len(children) == 3:
			args = ast.arguments(None, None, None, None, None, None, None, None, lambdef_node)
		else:
			args = self.handle_varargslist(children[1])
		return ast.Lambda(args, expr, lambdef_node)

	
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
			tmp_atom_expr.startpos = atom_expr.startpos
			tmp_atom_expr.endpos = atom_expr.endpos
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
				#return self.handle_call(children[1], left_expr)
				bases, keywords, starargs, kwargs = self.handle_arglist(children[1])
				return ast.Call(left_expr, bases, keywords, starargs, kwargs, trailer_node)
		elif first_child.type == self.tokens.DOT:
			attr = children[1].value
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

	'''
	def handle_call(self, args_node, callable_expr):
		#FIXME needs rewrite for python3
		arg_count = 0
		keyword_count = 0
		generator_count = 0
		children = self.children(args_node)
		for argument in children:
			arg_children = self.children(argument)
			if argument.type == self.syms.argument:
				if len(children) == 1:
					arg_count += 1
				elif children[1].type == self.syms.comp_for:
					generator_count += 1
				else:
					keyword_count += 1
		if generator_count > 1 or \
				(generator_count and (keyword_count or arg_count)):
			self.error("Generator expression must be parenthesized "
					   "if not sole argument", args_node)
		if arg_count + keyword_count + generator_count > 255:
			self.error("more than 255 arguments", args_node)
		args = []
		keywords = []
		used_keywords = {}
		variable_arg = None
		keywords_arg = None
		child_count = len(children)
		i = 0
		while i < child_count:
			argument = children[i]
			if argument.type == self.syms.argument:
				if len(children) == 1:
					expr_node = children[0]
					if keywords:
						self.error("non-keyword arg after keyword arg",
								   expr_node)
					args.append(self.handle_expr(expr_node))
				elif children[1].type == self.syms.comp_for:
					args.append(self.handle_genexp(argument))
				else:
					keyword_node = children[0]
					keyword_expr = self.handle_expr(keyword_node)
					if isinstance(keyword_expr, ast.Lambda):
						self.error("lambda cannot contain assignment",
								   keyword_node)
					elif not isinstance(keyword_expr, ast.Name):
						self.error("keyword can't be an expression",
								   keyword_node)
					keyword = keyword_expr.id
					if keyword in used_keywords:
						self.error("keyword argument repeated", keyword_node)
					used_keywords[keyword] = None
					#self.check_forbidden_name(keyword, keyword_node)
					keyword_value = self.handle_expr(children[2])
					keywords.append(ast.keyword(keyword, keyword_value, keyword_node))
			elif argument.type == self.tokens.STAR:
				variable_arg = self.handle_expr(children[i + 1])
				i += 1
			elif argument.type == self.tokens.DOUBLESTAR:
				keywords_arg = self.handle_expr(children[i + 1])
				i += 1
			else:
				raise AssertionError("Unknown callable")
			i += 1
		if not args:
			args = None
		if not keywords:
			keywords = None
		return ast.Call(callable_expr, args, keywords, variable_arg,
						keywords_arg, callable_expr)
	'''

	def parse_number(self, raw):
		try:
			return int(raw)
		except ValueError:
			if raw.startswith('0x'):
				return int(raw[2:], 16)
			elif raw.startswith('Oo'):
				return int(raw[2:], 8)
			elif raw.startswith('Ob'):
				return int(raw[2:], 2)


	def handle_atom(self, atom_node):
		#self.pretty_print(atom_node)
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
		elif first_child_type == self.tokens.BACKQUOTE:
			expr = self.handle_testlist(children[1])
			return ast.Repr(expr, atom_node)
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
		current_for = comp_node.children[1]
		while True:
			count += 1
			if len(current_for.children) == 5:
				current_iter = current_for.children[4]
			else:
				return count
			while True:
				first_child = current_iter.children[0]
				if first_child.type == for_type:
					current_for = current_iter.children[0]
					break
				elif first_child.type == if_type:
					if len(first_child.children) == 3:
						current_iter = first_child.children[2]
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

	#@specialize.arg(5)
	def comprehension_helper(self, comp_node, for_type, if_type, iter_type,
							 handle_source_expression):
		elt = self.handle_expr(comp_node.children[0])
		fors_count = self.count_comp_fors(comp_node, for_type, if_type)
		comps = []
		comp_for = comp_node.children[1]
		for i in range(fors_count):
			for_node = comp_for.children[1]
			for_targets = self.handle_exprlist(for_node, ast.Store)
			expr = handle_source_expression(comp_for.children[3])
			assert isinstance(expr, ast.expr)
			if len(for_node.children) == 1:
				comp = ast.comprehension(for_targets[0], expr, None, comp_for)
			else:
				target = ast.Tuple(for_targets, ast.Store, comp_for)
				comp = ast.comprehension(target, expr, None, comp_node)
			if len(comp_for.children) == 5:
				comp_for = comp_iter = comp_for.children[4]
				assert comp_iter.type == iter_type
				ifs_count = self.count_comp_ifs(comp_iter, for_type)
				if ifs_count:
					ifs = []
					for j in range(ifs_count):
						comp_for = comp_if = comp_iter.children[0]
						ifs.append(self.handle_expr(comp_if.children[1]))
						if len(comp_if.children) == 3:
							comp_for = comp_iter = comp_if.children[2]
					comp.ifs = ifs
				if comp_for.type == iter_type:
					comp_for = comp_for.children[0]
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
		return exprs


