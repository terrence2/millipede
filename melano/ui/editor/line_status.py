from PyQt4.QtGui import QWidget, QPainter, QIcon, QColor
from melano.ui.editor.edit import MelanoCodeEdit


class MelanoCodeLineStatus(QWidget):
	def __init__(self, edit:MelanoCodeEdit, parent:QWidget):
		super().__init__(parent)
		self.edit = edit

		# TODO: set fixed width font?

		# update the width in real-time by monitoring doc changes
		self._prior_linecount = 0
		self.edit.document().contentsChanged.connect(self.onDocContentsChanged)
		self.onDocContentsChanged()
		
		# connect scrollbar events to updates on this widget
		self.edit.verticalScrollBar().valueChanged.connect(self.update)

		# connect cursor position updates to updates on this widget
		self.edit.cursorPositionChanged.connect(self.update)		

		# containers for error and warning lines
		self._errors = {}
		self._warnings = {}
		
		self._errors[3] = "Foobar!"
		self._warnings[6] = "Barfoo!"

		# load icons
		self._icon_error = QIcon.fromTheme("dialog-error")
		self._icon_warning = QIcon.fromTheme("dialog-warning")


	def add_error(self, lineno:int, message:str):
		self._errors[lineno] = message
	
	def clear_errors(self):
		self._errors = {}

	
	def add_warning(self, lineno:int, message:str):
		self._warnings[lineno] = message
	
	def clear_warnings(self):
		self._warnings = {}
	

	def onDocContentsChanged(self):
		line_count = self.edit.document().blockCount()
		width = self.fontMetrics().width(str(line_count))
		self.setFixedWidth(width + 16)
		if line_count != self._prior_linecount:
			self._prior_linecount = line_count
			self.update()


	def paintEvent(self, ev):
		p = QPainter(self)
		fmetrics = self.fontMetrics()
		font_ascent = fmetrics.ascent()
		font_height = fmetrics.ascent() + fmetrics.descent() + 1
		font_extra = fmetrics.descent() / 2 # 0-9 has no descenders, so spread it above too
		doc = self.edit.document()
		layout = doc.documentLayout()
		start_pos = self.edit.verticalScrollBar().value()
		end_pos = start_pos + self.edit.viewport().height()
		cursor_lineno = self.edit.textCursor().blockNumber()

		blk = doc.begin()
		lineno = 1
		while blk and blk.isValid():
			blk_bounds = layout.blockBoundingRect(blk)
			pos = blk_bounds.y()

			if pos + blk_bounds.height() >= start_pos and pos <= end_pos:
				txt = str(lineno)
				centering = (blk_bounds.height() - font_height) / 2
				p.drawText(self.width() - fmetrics.width(txt), 
					round(pos - centering - start_pos + font_ascent + font_extra),
					txt)
			
				if lineno in self._errors:
					centering = (blk_bounds.height() - font_height) / 2
					self._icon_error.paint(p, 0, round(pos + centering), 16, 16)

				elif lineno in self._warnings:
					centering = (blk_bounds.height() - font_height) / 2
					self._icon_warning.paint(p, 0, round(pos + centering), 16, 16)
			
			lineno += 1
			blk = blk.next()


