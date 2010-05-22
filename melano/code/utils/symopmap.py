'''
This is a map in the sense of buried pirate treasure.  It tells us about the
sequence of name->symbols {un}mapping actions in each scope.
'''
__author__ = 'Terrence Cole <terrence@zettabytestorage.com>'

from melano.parser.common.ast import AST, Load, Store, Del
from melano.parser.common.visitor import ASTVisitor
from melano.util.fwddecl import fwddecl
from collections import OrderedDict


class SymbolAction:
	'''Track an action that occurs on a name.  These go in an ordered dict as
		keys, so we keep an order parameter that we bump with each duplicate.
	'''
	def __init__(self, name:str, op:int):
		self.name = name
		self.op = op
		self.order = 0 # increment on collision

	def __hash__(self):
		return hash(self.name) + hash(self.op) + hash(self.order)
	

class SymbolOpMap(metaclass=fwddecl):
	'''Track an ordered list of mappings from symbol actions to action results.
		An action result may be a new symbol map or an AST node.
	'''
	def __init__(self, node:AST, parent:SymbolOpMap=None):
		self.node = node
		self.parent = parent
		self.mappings = OrderedDict()
	
	
	def update(self, symaction:SymbolAction, result):
		while symaction in self.mappings:
			symaction.order += 1
		self.mappings[symaction] = result


	def as_string(self, level:int=0):
		pad = '\t' * level
		out = ''
		for sym, res in self.mappings.items():
			# get the action type
			act = ' <- '
			if sym.op == Load:
				act = ' -> '
			# build the action string
			out += pad + sym.name + act + res.__class__.__name__ + '\n'
			# recurse if needed
			if isinstance(res, SymbolOpMap):
				out += res.as_string(level + 1)
		return out
		

class ModuleScope(SymbolOpMap):
	pass


class ClassScope(SymbolOpMap):
	pass


class FunctionScope(SymbolOpMap):
	pass




class SymbolOpMapBuilder(ASTVisitor):
	def __init__(self):
		self.opmap = None
		self.context = None


	def visit_Module(self, node):
		assert self.opmap is None
		self.context = self.opmap = ModuleScope(node, parent=None)
		self.generic_visit(node)
		

	def __flatten_attr(self, node):
		if node.__class__.__name__ == 'Attribute':
			return self.__flatten_attr(node.value) + '.' + node.attr
		elif node.__class__.__name__ == 'Name':
			return node.id
		elif node.__class__.__name__ == 'str':
			return node
		raise AssertionError("Unknown name type: {}".format(node))


	def visit_Import(self, node):
		for alias in node.names:
			name = alias.asname or alias.name
			sym = SymbolAction(self.__flatten_attr(name), Store)
			self.context.update(sym, node)


	def visit_ImportFrom(self, node):
		for alias in node.names:
			#module_path = self.locate_module(node.module, node.level)
			#module = MelanoCodeUnit(module_path)
			if alias.name == '*':
				#names = module.get_exported_named()
				#for name in names:
				#	self.symtable.bind(name, module)
				raise NotImplementedError()
			else:
				name = alias.asname or alias.name
				sym = SymbolAction(self.__flatten_attr(name), Store)
				self.context.update(sym, node)


	def visit_ClassDef(self, node):
		scope = ClassScope(node, self.context)
		sym = SymbolAction(node.name, Store)

		# bases are evaluated in the enclosing namespace
		if node.bases:
			for base in node.bases:
				self.visit(base)
		if node.starargs:
			self.visit(node.starargs)
		if node.keywords:
			for kw in node.keywords:
				self.visit(kw)
		if node.kwargs:
			self.visit(node.kwargs)

		# push the class scope
		self.context.update(sym, scope)
		self.context = scope

		# evaluate the class body
		for child in node.body:
			self.visit(child)

		# pop the class scope
		self.context = self.context.parent

		# decorators run after the class def, out of the class scope
		if node.decorator_list:
			for deco in node.decorator_list:
				self.visit(deco)


	def visit_FunctionDef(self, node):
		scope = FunctionScope(node, self.context)
		sym = SymbolAction(node.name, Store)

		# annotations and defaults are evaluated in enclosing context
		if node.returns:
			self.visit(node.returns)
		for arg in node.args.args:
			if arg.annotation:
				self.visit(arg.annotation)
		if node.args.varargannotation:
			self.visit(node.args.varargannotation)
		for arg in node.args.kwonlyargs:
			self.visit(arg.annotation)
		if node.args.kwargannotation:
			self.visit(node.args.kwargannotation)
		for expr in node.args.defaults:
			self.visit(expr)
		for expr in node.args.kw_defaults:
			self.visit(expr)

		# push the function scope
		self.context.update(sym, scope)
		self.context = scope

		# evaluate function body
		for stmt in node.body:
			self.visit(stmt)

		# pop functions scope		
		self.context = self.context.parent

		# decorators are visited in enclosing scope, after evaluating sub-scope
		if node.decorator_list:
			for deco in node.decorator_list:
				self.visit(deco)


	def visit_Global(self, node):
		print("GLOBAL")
		self.generic_visit(node)

	def visit_NonLocal(self, node):
		print("NONLOCAL")
		self.generic_visit(node)

	def visit_ListComp(self, node):
		print("LISTCOMP")
		self.generic_visit(node)

	def visit_DictComp(self, node):
		print("DICTCOMP")
		self.generic_visit(node)

	def visit_SetComp(self, node):
		print("SETCOMP")
		self.generic_visit(node)

	def visit_GeneratorExp(self, node):
		print("GENERATOR")
		self.generic_visit(node)

	def visit_Lambda(self, node):
		print("LAMBDA")
		self.generic_visit(node)

	def visit_For(self, node):
		print("FOR")
		self.generic_visit(node)

	def visit_Assign(self, node):
		print("ASSIGN")
		self.generic_visit(node)

	def visit_AugAssign(self, node):
		print("AUG ASSIGN")
		self.generic_visit(node)

	def visit_Name(self, node):
		sym = SymbolAction(node.id, node.ctx)
		self.context.update(sym, node)


