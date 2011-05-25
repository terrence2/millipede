'''
Copyright (c) 2011, Terrence Cole.
All rights reserved.
'''
from contextlib import contextmanager
from melano.hl.nodes.builtins import Builtins
from melano.hl.cfg.basicblock import BasicBlock
from melano.hl.nodes.module import MpModule
from melano.lang.visitor import ASTVisitor
import melano.py.ast as py
import pdb


class CFGBuilder(ASTVisitor):
	'''
	TODO:
	- break/continue in a block need cause enclosing block to not emit normal exit path
	'''

	def __init__(self, project):
		super().__init__()

		self.project = project

		self.ctx = None

		# each loop adds the node id to this stack, break and continue statements record the current context
		#		into the break and continue context lists under the topmost loop id, so that when we get back to
		#		the loop context, we can add an edge from the current context to the proper head or tail. 
		self.loop_stack = []
		self.break_contexts = {}
		self.continue_contexts = {}

		# all control-flow-graphs that we find
		self.cfg = None


	@contextmanager
	def set_context(self, bb):
		prior = self.ctx
		self.ctx = bb
		yield
		self.ctx = prior


	@contextmanager
	def loop(self, node):
		self.loop_stack.append(id(node))
		yield
		self.loop_stack.pop()


	def get_loop_escapes(self, node):
		breaks = self.break_contexts.get(id(node), None)
		continues = self.continue_contexts.get(id(node), None)
		if breaks: del self.break_contexts[id(node)]
		if continues: del self.continue_contexts[id(node)]
		return breaks, continues


	def bb_from_nodelist(self, bb, body):
		'''Traverses body, visiting children, breaking the given body into basic blocks as children of bb, as we go.
			Returns the trailer bb.  Creates a trailer if there is not one.  On exit the ctx is the tail.  We also return this.'''
		self.ctx = bb
		for node in body:
			next_nodes = self.visit(node)

			# if we visit a node that creates a new basic block(s) (e.g. if) we need to create a new basic block
			#	that is parented by the exit from the returned block(s) -- parenting of the created blocks is handled
			# by the block creator.
			if next_nodes:
				self.ctx = BasicBlock(bb.label, *next_nodes)
				for n in next_nodes:
					n.children.append(self.ctx)

			# if we visited a node that breaks the flow of this block, we don't have to continue
			#		processing nodes here
			if isinstance(node, (py.Break, py.Continue)):
				#FIXME: need to extend this with other flow control that gets handled by other, non-local nodes?
				#FIXME: we need to avoid setting our normal tails from this bb, since there is only the break/continue
				#, py.Raise, py.Return)):
				return None

		return self.ctx


	########  Create new CFG's ########
	def visit_Module(self, node):
		is_main = self.cfg is None

		node.bb = node.hl.cfg = BasicBlock('module')
		if is_main:
			self.cfg = node.bb
		tail = self.bb_from_nodelist(node.bb, node.body)

		if is_main:
			node.bb.is_head = True
			tail.is_tail = True
			self.cfg = node.bb
			self.cfg_tail = tail

		return [tail]


	def visit_ClassDef(self, node):
		self.visit(node.name)
		self.visit_nodelist(node.bases)
		self.visit_nodelist(node.keywords)
		self.visit(node.starargs)
		self.visit(node.kwargs)

		node.bb = node.hl.cfg = BasicBlock('class')
		with self.set_context(node.bb):
			tail = self.bb_from_nodelist(node.bb, node.body)

		self.visit_nodelist(node.decorator_list)


	def visit_FunctionDef(self, node):
		# annotations
		self.visit(node.returns)
		self.visit_nodelist_field(node.args.args, 'annotation') # position arg annotations
		self.visit(node.args.varargannotation) # *args annotation
		self.visit_nodelist_field(node.args.kwonlyargs, 'annotation') # kwargs annotation
		self.visit(node.args.kwargannotation) # **args annotation
		# defaults
		self.visit_nodelist(node.args.defaults) # positional arg default values
		self.visit_nodelist(node.args.kw_defaults) # kwargs default values
		# name
		self.visit(node.name)

		node.bb = node.hl.cfg = BasicBlock('function')
		with self.set_context(node.bb):
			# args
			self.visit_nodelist_field(node.args.args, 'arg')
			self.visit(node.args.vararg)
			self.visit_nodelist_field(node.args.kwonlyargs, 'arg')
			self.visit(node.args.kwarg)

			# body
			tail = self.bb_from_nodelist(node.bb, node.body)

		# decorators
		# Note: see ClassDef note on decorators
		self.visit_nodelist(node.decorator_list)


	def _maybe_run_module(self, mod):
		# for non-local imports, insert a dummy BasicBlock
		if not self.project.is_local(mod):
			return None

		# otherwise, load the cfg if it is our first time, otherwise, we will skip out with the cached copy
		tail = None
		if not mod.cfg:
			with self.set_context(self.ctx):
				tail = self.visit(mod.ast)

			# add a link to the sub-cfg
			self.ctx.children.append(mod.cfg)
			mod.cfg.parents.append(self.ctx)

		return tail


	def visit_Import(self, node):
		for i, alias in enumerate(node.names):
			if alias.asname:
				mod = alias.asname.hl.scope
			elif isinstance(alias.name, py.Attribute):
				mod = alias.name.attr.hl.scope
			else:
				mod = alias.name.hl.scope
			assert isinstance(mod, MpModule)

			# load the ast 
			tail = self._maybe_run_module(mod)
			if tail:
				# if we created a new sub-cfg, we need to create a new BB off of the tail to hold the name
				#		assignment in this scope
				self.ctx = BasicBlock('import-names', tail)

			# load names
			if alias.asname:
				self.visit(alias.asname)
			else:
				self.visit(alias.name)

		return tail


	def visit_ImportFrom(self, node):
		tail = self._maybe_run_module(node.module.hl)

		for alias in node.names:
			if alias.asname:
				self.visit(alias.asname)
			else:
				if alias.name == '*':
					# TODO: need to load all names inline here
					raise NotImplementedError
				self.visit(alias.name)

		return tail


	########  Flow control commands ########
	def visit_Break(self, node):
		top = self.loop_stack[-1]
		if top not in self.break_contexts:
			self.break_contexts[top] = [self.ctx]
		else:
			self.break_contexts[top].append(self.ctx)


	def visit_Continue(self, node):
		top = self.loop_stack[-1]
		if top not in self.continue_contexts:
			self.continue_contexts[top] = [self.ctx]
		else:
			self.continue_contexts[top].append(self.ctx)


	def visit_Return(self):
		raise NotImplementedError


	def visit_Yield(self):
		raise NotImplementedError


	########  Handle control flow ########
	def visit_Call(self, node):
		'''Lookup the called node: it should have a function or class with __call__ as a target, and it should have been 
			visited, since we are following imports.  We just need to add a link from ctx to this and return it as a new tail.
		'''
		# parameters are all loaded in current context
		self.visit_nodelist(node.args)
		self.visit(node.starargs)
		self.visit_nodelist(node.keywords)
		self.visit(node.kwargs)

		# name is loaded in current context
		self.visit(node.func)

		# defined internally in a way we can access
		if node.hl.ref.scope:
			assert node.hl.ref.scope.cfg is not None
			self.ctx.children.append(node.hl.ref.scope.cfg)
			self.ctx = node.hl.ref.scope.cfg
			return [node.hl.ref.scope.cfg]
		else:
			pass
			#assert isinstance(node.hl.ref.parent, Builtins)
			#FIXME: we can probably do something clever here to encapsulate our knowledge of each builtin



	def visit_If(self, _node):
		'''Elif blocks are nested in the ast, but we need the elif truth completion to back out all the way
			to the toplevel context on exit, not the nested context.  Therefore we have to special case
			the elif blocks and _not_ call this function recursively, as we naively would.  On the other hand,
			we _do_ want the elif tests to run only on failure of the prior test, so those need to go in a
			nested block in the failure case of the prior if, so we can't just make this fully flat.
		'''
		tails = []
		def _if_handler(node):
			self.visit(node.test)

			# create blocks, both linked off of _current_ context
			node.bb = bb_true = BasicBlock('if-true', self.ctx)
			self.ctx.children.append(bb_true)
			if node.orelse:
				node.bb_else = bb_false = BasicBlock('if-false', self.ctx)
				self.ctx.children.append(bb_false)
			else:
				# fallthrough on if-false, if we have no orelse block to run
				tails.append(self.ctx)

			# build iftrue nodelist -- tail is self.ctx on exit
			tail = self.bb_from_nodelist(bb_true, node.body)
			if tail:
				tails.append(tail)

			# build elif nodelist
			if node.orelse and len(node.orelse) == 1 and isinstance(node.orelse[0], py.If):
				self.ctx = bb_false
				_if_handler(node.orelse[0])

			# build else nodelist
			elif node.orelse:
				tail = self.bb_from_nodelist(bb_false, node.orelse)
				tails.append(tail)

		_if_handler(_node)
		return tails



	def visit_For(self, node):
		'''See comment on visit_While, as it holds true here also.'''
		tails = []

		self.visit(node.iter)

		# add links from ctx to out
		node.bb = BasicBlock('for-body', self.ctx)
		self.ctx.children.append(node.bb)
		if node.orelse:
			node.bb_else = BasicBlock('for-else', self.ctx)
			self.ctx.children.append(node.bb_else)
		else:
			tails.append(self.ctx)

		# visit the loop body
		with self.set_context(node.bb):
			self.visit(node.target)
			with self.loop(node):
				body_tail = self.bb_from_nodelist(node.bb, node.body)
			breaks, continues = self.get_loop_escapes(node)

		# add all contexts that break to the tail
		if breaks:
			tails.extend(breaks)

		# all contexts with a continue need to loop back to the body start directly
		if continues:
			node.bb.children.extend(continues)

		# body's tail block always links to itself
		body_tail.children.append(node.bb)

		# visit else
		if node.orelse:
			# if we have an else, we can always reach it (break or no)
			body_tail.children.append(node.bb_else)

			with self.set_context(node.bb_else):
				else_tail = self.bb_from_nodelist(node.bb_else, node.orelse)
				tails.append(else_tail) # else always links out

		else:
			# no else means body always falls through to tail
			tails.append(body_tail)

		return tails


	def visit_While(self, node):
		'''
		Test is evaluated in both the enclosing block and in the body block.
		
		The enclosing block will always link to the body and will link to one of to else (if present) or the tail.
		#FIXME: if we add some static proto-evaluation, then we can make this more precise

		The body will always link to itself and one of either else or tail.  The conditions are complicated.
		if orelse not present - jump only to tail
		if orelse present and no break - jump only to else
		else jump to both

		The else always links to the tail
		'''
		tails = []
		self.visit(node.test)

		# add links from ctx out
		node.bb = BasicBlock('while', self.ctx)
		self.ctx.children.append(node.bb)
		if node.orelse:
			node.bb_else = BasicBlock('while-else', self.ctx)
			self.ctx.children.append(node.bb_else)
		else:
			tails.append(self.ctx) # no else means we can fall all the way through to tail

		# visit children, discover break and continue points		
		with self.set_context(node.bb):
			self.visit(node.test)
			with self.loop(node):
				body_tail = self.bb_from_nodelist(node.bb, node.body)
			breaks, continues = self.get_loop_escapes(node)

		# add all contexts that break to the tail
		if breaks:
			tails.extend(breaks)

		# all contexts with a continue need to loop back to the body start directly
		if continues:
			node.bb.children.extend(continues)

		# body's tail block always links to itself
		body_tail.children.append(node.bb)

		# visit else
		if node.orelse:
			# if we have an else, we can always reach it (break or no)
			body_tail.children.append(node.bb_else)

			with self.set_context(node.bb_else):
				else_tail = self.bb_from_nodelist(node.bb_else, node.orelse)
				tails.append(else_tail) # else always links out

		else:
			# no else means body always falls through to tail
			tails.append(body_tail)

		return tails


	def visit_TryFinally(self, node):
		pdb.set_trace()

	########  Updates the action list ########
	def visit_Name(self, node):
		if node.ctx == py.Aug:
			self.ctx.add_action(py.Load, node.hl.deref())
			self.ctx.add_action(py.Store, node.hl.deref())
		elif node.ctx == py.Param:
			self.ctx.add_action(py.Store, node.hl.deref())
		elif node.ctx == py.Del:
			self.ctx.add_action(py.Store, node.hl.deref())
		else:
			self.ctx.add_action(node.ctx, node.hl.deref())



	########  Override these to change the visitation order ########
	def visit_AugAssign(self, node):
		self.visit(node.value)
		self.visit(node.target)

	def visit_Assign(self, node):
		self.visit(node.value)
		self.visit_nodelist(node.targets)

