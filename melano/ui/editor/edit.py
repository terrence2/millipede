from .document import MelanoCodeDocument
from PyQt4.QtGui import QTextEdit, QTextOption, QTextCursor, QTextFormat, QColor, QToolTip
from PyQt4.QtCore import QEvent
from melano.hl.name import Name
#from melano.code.symbols.symbol import Symbol
#from melano.code.symbols.function import Function


class MelanoCodeEdit(QTextEdit):
	def __init__(self, doc:MelanoCodeDocument, parent):
		super().__init__(parent)

		self.setDocument(doc)
		self.setTabStopWidth(24) # NOTE: doc has to be set first
		self.setWordWrapMode(QTextOption.NoWrap)

		# highlight the current line on changes
		self.cursorPositionChanged.connect(self.onCursorPositionChanged)

	def event(self, e):
		if e.type() == QEvent.ToolTip:
			print("GOT EVENT:", str(e.type()))
			cursor = self.cursorForPosition(e.pos())
			cursor.select(QTextCursor.WordUnderCursor)
			if cursor.selectedText():
				QToolTip.showText(e.globalPos(), cursor.selectedText())
			else:
				QToolTip.hideText()
			return True
		return super().event(e)


	def show_symbol(self, symbol:Name):
		if not symbol: return

		node = symbol.node
		if not node:
			return

		#if isinstance(node, ast.FunctionDef):
		#	node = node.name # go to function name, not 'def'

		cursor = self.document().select_ast_node(node)
		self.setTextCursor(cursor)


	def onCursorPositionChanged(self):
		selection = QTextEdit.ExtraSelection()

		clr = QColor.fromRgb(*(0xF0,) * 3)
		selection.format.setBackground(clr)
		selection.format.setProperty(QTextFormat.FullWidthSelection, True)
		selection.cursor = self.textCursor()
		selection.cursor.clearSelection()

		self.setExtraSelections([selection])


