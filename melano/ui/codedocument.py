from PyQt4 import QtCore
from PyQt4.QtCore import QCoreApplication
from PyQt4.QtGui import QTextDocument
import tokenize


class MelanoCodeDocument(QTextDocument):
	def __init__(self, parent):
		super().__init__(parent)
		self.contentsChange.connect(self.onContentsChange)

		self.config = QCoreApplication.instance().config
		self.tokenizer = self.config.interpreters['3.1'].parser.tokenizer


	@QtCore.pyqtSlot(int, int, int)
	def onContentsChange(self, a, b, c):
		#print("HELLO WORLD!", a, b, c)
		try:
			tokens = self.tokenizer.tokenize(self.toPlainText())
		except tokenize.TokenError:
			return
		
		RESERVED = set([
			'False',      'class',      'finally',    'is',         'return',
			'None',       'continue',   'for',        'lambda',     'try',
			'True',       'def',        'from',       'nonlocal',   'while',
			'and',        'del',        'global',     'not',        'with',
			'as',         'elif',       'if',         'or',         'yield',
			'assert',     'else',       'import',     'pass',
			'break',      'except',     'in',         'raise'
		])

		for tok in tokens:
			if tok.type == 1:
				if tok.string in RESERVED:
					print(tok)
		
