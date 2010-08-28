from PyQt4.QtGui import QTextEdit, QTextOption, QTextCursor
from melano.code.symbols.symbol import Symbol
from melano.code.symbols.function import Function
from .document import MelanoCodeDocument


class MelanoCodeEdit(QTextEdit):
	def __init__(self, parent):
		super().__init__(parent)
	
		self.setTabStopWidth(1) #FIXME: not working!
		self.setWordWrapMode(QTextOption.NoWrap)
	
		
	def show_symbol(self, symbol:Symbol):
		if not symbol.get_ast_node():
			return

		node = symbol.get_ast_node()
		if isinstance(symbol, Function):
			node = node.name # go to function name, not 'def'
		
		cursor = self.textCursor()
		
		s = node.startpos
		e = node.endpos
		spos = self.document().findBlockByLineNumber(s[0] - 1).position() + s[1]
		epos = self.document().findBlockByLineNumber(e[0] - 1).position() + e[1]
		cursor.setPosition(spos, QTextCursor.MoveAnchor)
		cursor.setPosition(epos, QTextCursor.KeepAnchor)
		
		self.setTextCursor(cursor)
