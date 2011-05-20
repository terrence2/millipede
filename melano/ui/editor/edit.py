from .document import MpCodeDocument
from PyQt4.QtCore import QCoreApplication, QEvent
from PyQt4.QtGui import QTextEdit, QTextOption, QTextCursor, QTextFormat, QColor, \
	QToolTip
from melano.hl.name import Name
from melano.py import ast
from melano.util.debug import qt_debug
#from melano.code.symbols.symbol import Symbol
#from melano.code.symbols.function import Function


class MpCodeEdit(QTextEdit):
	def __init__(self, doc:MpCodeDocument, parent):
		super().__init__(parent)

		self.setDocument(doc)
		self.setTabStopWidth(24) # NOTE: doc has to be set first
		self.setWordWrapMode(QTextOption.NoWrap)

		# highlight the current line on changes
		self.cursorPositionChanged.connect(self.onCursorPositionChanged)

	def event(self, e):
		if e.type() == QEvent.ToolTip:
			cursor = self.cursorForPosition(e.pos())
			cursor.select(QTextCursor.WordUnderCursor)
			if cursor.selectedText():
				# discover where our text is in the document
				ln = cursor.block().firstLineNumber() + 1
				col_end = cursor.position() - cursor.block().position()
				content = cursor.selectedText()
				col_start = max(1, col_end - len(content))
				print('hover:', ln, str(col_start) + '->' + str(col_end), content)

				# map to an ast node and format a tooltip
				tooltip = QCoreApplication.instance().on_hover_text(self.document().module, (ln, col_start), (ln, col_end), content)

				# show the tooltip
				if tooltip:
					QToolTip.showText(e.globalPos(), tooltip)
			else:
				QToolTip.hideText()
			return True
		return super().event(e)


	def show_symbol(self, symbol:Name):
		if not symbol: return

		node = symbol.ast
		if not node:
			return

		if isinstance(node, ast.FunctionDef):
			node = node.name # go to function name, not 'def'

		cursor = self.document().select_ast_node(node)
		self.setTextCursor(cursor)


	def onCursorPositionChanged(self):
		# paint a different background color on the line that contains the cursor
		selection = QTextEdit.ExtraSelection()
		clr = QColor.fromRgb(*(0xF0,) * 3)
		selection.format.setBackground(clr)
		selection.format.setProperty(QTextFormat.FullWidthSelection, True)
		selection.cursor = self.textCursor()
		selection.cursor.clearSelection()
		self.setExtraSelections([selection])


