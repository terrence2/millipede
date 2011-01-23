import tokenize
from PyQt4 import QtCore
from PyQt4.QtCore import QCoreApplication
from PyQt4.QtGui import QTextDocument, QTextCursor, QColor
from melano.parser.tokens import python_tokens


RESERVED = set([
	'class', 'finally', 'is', 'return',
	'continue', 'for', 'lambda', 'try',
	'def', 'from', 'nonlocal', 'while',
	'and', 'del', 'global', 'not', 'with',
	'as', 'elif', 'if', 'or', 'yield',
	'assert', 'else', 'import', 'pass',
	'break', 'except', 'in', 'raise'
])
EXCEPTIONS = set([
	'ArithmeticError', 'AssertionError', 'AttributeError',
	'BaseException', 'BufferError', 'BytesWarning',
	'DeprecationWarning', 'EOFError', 'Ellipsis', 'EnvironmentError',
	'Exception', 'False', 'FloatingPointError', 'FutureWarning',
	'GeneratorExit', 'IOError', 'ImportError', 'ImportWarning',
	'IndentationError', 'IndexError', 'KeyError', 'KeyboardInterrupt',
	'LookupError', 'MemoryError', 'NameError', 'NotImplementedError',
	'OSError', 'OverflowError', 'PendingDeprecationWarning',
	'ReferenceError', 'RuntimeError', 'RuntimeWarning', 'StopIteration',
	'SyntaxError', 'SyntaxWarning', 'SystemError', 'SystemExit',
	'TabError', 'TypeError', 'UnboundLocalError', 'UnicodeDecodeError',
	'UnicodeEncodeError', 'UnicodeError', 'UnicodeTranslateError',
	'UnicodeWarning', 'UserWarning', 'ValueError', 'Warning',
	'ZeroDivisionError',
])
CONSTANTS = set([
	'Ellipsis', 'NotImplemented', 'False', 'None', 'True', '__debug__',
])
META = set([
	'__doc__', '__import__', '__name__', '__package__',
])
BUILTIN = set([
	'abs', 'all', 'any', 'ascii', 'bin', 'bool', 'bytearray', 'bytes',
	'chr', 'classmethod', 'compile', 'complex', 'delattr', 'dict',
	'dir', 'divmod', 'enumerate', 'eval', 'exec', 'filter', 'float',
	'format', 'frozenset', 'getattr', 'globals', 'hasattr', 'hash',
	'help', 'hex', 'id', 'input', 'int', 'isinstance', 'issubclass',
	'iter', 'len', 'list', 'locals', 'map', 'max', 'memoryview', 'min',
	'next', 'object', 'oct', 'open', 'ord', 'pow', 'print', 'property',
	'range', 'repr', 'reversed', 'round', 'set', 'setattr', 'slice',
	'sorted', 'staticmethod', 'str', 'sum', 'super', 'tuple', 'type',
	'vars', 'zip'
])
TOKEN_CLASSES = [
	(RESERVED, 		500, QColor.fromRgbF(0.7, 0.05, 0.05)),
	(EXCEPTIONS, 	400, QColor.fromRgbF(0.3, 0.1, 0.1)),
	(CONSTANTS, 	600, QColor.fromRgbF(0.1, 0.1, 0.3)),
	(META, 			300, QColor.fromRgbF(0.8, 0.0, 0.8)),
	(BUILTIN, 		350, QColor.fromRgbF(0.1, 0.6, 0.5)),
]
IGNORE_TOKENS = set([
	python_tokens['NEWLINE'],
	python_tokens['NL'],
	python_tokens['INDENT'],
	python_tokens['DEDENT']
])


class MelanoCodeDocument(QTextDocument):
	def __init__(self, module, parent):
		self.module = module
		self.filename = module.filename
		with open(self.filename, 'rb') as fp:
			data = fp.read()
		# FIXME: detect and handle encoding
		super().__init__(data.decode('utf-8'), parent)
		self.setModified(False)

		self.contentsChange.connect(self.onContentsChange)

		self.project = QCoreApplication.instance().project
		self.tokenizer = self.project.parser_driver.tokenizer


	def select_ast_node(self, ast_node):
		return self.select_range(ast_node.start, ast_node.end)

	def select_token(self, token):
		return self.select_range(token.start, token.end)

	def select_range(self, s, e):
		cursor = QTextCursor(self)

		spos = self.findBlockByLineNumber(s[0] - 1).position() + s[1]
		epos = self.findBlockByLineNumber(e[0] - 1).position() + e[1]
		cursor.setPosition(spos, QTextCursor.MoveAnchor)
		cursor.setPosition(epos, QTextCursor.KeepAnchor)

		return cursor


	@QtCore.pyqtSlot(int, int, int)
	def onContentsChange(self, a, b, c):
		print(a, b, c)

		try:
			tokens = self.tokenizer.tokenize(self.toPlainText())
		except tokenize.TokenError:
			return

		for tok in tokens:
			if tok.type == python_tokens['NAME']:
				for words, weight, color in TOKEN_CLASSES:
					if tok.string in words:
						cursor = self.select_token(tok)
						fmt = cursor.charFormat()
						fmt.setFontWeight(weight)
						fmt.setForeground(color)
						cursor.setCharFormat(fmt)
			elif tok.type == python_tokens['COMMENT']:
				cursor = self.select_token(tok)
				fmt = cursor.charFormat()
				fmt.setForeground(QColor.fromRgbF(0.0, 0.0, 0.9))
				cursor.setCharFormat(fmt)
			elif tok.type == python_tokens['STRING']:
				cursor = self.select_token(tok)
				fmt = cursor.charFormat()
				fmt.setForeground(QColor.fromRgbF(0.0, 0.0, 0.9))
				cursor.setCharFormat(fmt)
			elif tok.type in IGNORE_TOKENS:
				pass
			else:
				#print(tok)
				pass


