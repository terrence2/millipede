'''
Nodes that comprise a Block Syntax Tree.
'''
__author__ = 'Terrence Cole <terrence@zettabytestorage.com>'

from melano.parser.common.ast import AST


class BST:
	'''
	Base class of all block types.  Takes and stores the underlying AST 
	reference.
	'''
	def __init__(self, ast:AST):
		self.ast = ast

		if len(ast.body) > 0 and \
			ast.body[0].__class__.__name__ == 'Expr' and \
			ast.body[0].value.__class__.__name__ == 'Str':
			self.docstring = ast.body[0].value.s
		else:
			self.docstring = None


class ModuleBlock(BST):
	def __init__(self, ast:AST):
		super().__init__(ast)
		self.imports = []
		self.functions = []
		self.classes = []
		
		self.all_imports = []
		self.all_functions = []
		self.all_methods = []
		self.all_classes = []

	def print_(self):
		print("Imports:")
		for imp in self.imports:
			for alias in imp.names:
				if not alias.asname:
					print("\t{}".format(str(alias.name)))
				else:
					print("\t{} as {}".format(str(alias.name), alias.asname))

		#print("Functions:")
		print("Classes:")
		for cls in self.classes:
			cls.print_(1)


class FunctionBlock(BST):
	def __init__(self, ast:AST):
		super().__init__(ast)

		self.returns = []
		self.yields = []
		self.raises = []

	def print_(self, level=0):
		pad = '\t' * level
		print(pad + "def " + self.ast.name)


class ClassBlock(BST):
	def __init__(self, ast:AST):
		super().__init__(ast)
		self.methods = []

	def print_(self, level=0):
		pad = '\t' * level
		print(pad + "class " + self.ast.name)
		for method in self.methods:
			method.print_(level + 1)


