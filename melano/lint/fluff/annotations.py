'''
Check that method have annotations.
'''
__author__ = 'Terrence Cole <terrence@zettabytestorage.com>'

from melano.parser.common.visitor import ASTVisitor 
from melano.lint.message import LintWarning

def analyse(unit):

	class AnnotationDetector(ASTVisitor):
		def __init__(self):
			self.messages = []
			self.has_return_value = False
	
		def visit_Return(self, node):
			if node.value is not None:
				self.has_return_value = True
	
		def visit_FunctionDef(self, node):
			if node.args.args:
				first = True
				for arg in node.args.args:
					if first and arg.arg == 'self':
						continue
					first = False
					if not arg.annotation:
						self.messages.append(
							LintWarning("argument '{}' missing annotation".format(arg.arg), 
								node.name, arg))

			if node.args.kwonlyargs:
				for arg in node.args.kwonlyargs:
					if not arg.annotation:
						self.messages.append(
							LintWarning("argument '{}' missing annotation".format(arg.arg), 
								node.name, arg))

			# scan for return stmts in the body
			for stmt in node.body:
				self.visit(stmt)

			# lower investigation should have revealed if we have a return value
			if self.has_return_value and not node.returns:
				self.messages.append(LintWarning('missing return type annotation', 
						node.name, node))

	visitor = AnnotationDetector()
	visitor.visit(unit.ast)
	return visitor.messages

