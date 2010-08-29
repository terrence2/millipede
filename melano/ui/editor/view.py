from PyQt4.QtGui import QTextEdit, QTextOption, QTextCursor
from melano.code.symbols.symbol import Symbol
from melano.code.symbols.function import Function
from .document import MelanoCodeDocument


class MelanoCodeEdit(QTextEdit):
	def __init__(self, doc:MelanoCodeDocument, parent):
		super().__init__(parent)

		self.setDocument(doc)
		self.setTabStopWidth(24) # NOTE: doc has to be set first
		self.setWordWrapMode(QTextOption.NoWrap)
	
		
	def show_symbol(self, symbol:Symbol):
		if not symbol.get_ast_node():
			return

		node = symbol.get_ast_node()
		if isinstance(symbol, Function):
			node = node.name # go to function name, not 'def'
		
		cursor = self.document().select_ast_node(node)
		self.setTextCursor(cursor)		
		

