from PyQt4.QtGui import QFrame, QWidget, QHBoxLayout
from melano.ui.editor.edit import MelanoCodeEdit
from melano.ui.editor.document import MelanoCodeDocument
from melano.ui.editor.line_status import MelanoCodeLineStatus


class MelanoCodeView(QFrame):
	def __init__(self, doc:MelanoCodeDocument, parent:QWidget):
		super().__init__(parent)
		self.setFrameStyle(QFrame.StyledPanel | QFrame.Sunken)
		self.setLineWidth(2)

		self.edit = MelanoCodeEdit(doc, self)

		self.status = MelanoCodeLineStatus(self.edit, self)
		
		self.box = QHBoxLayout(self)
		self.box.setSpacing(0)
		self.box.setMargin(0)
		self.box.addWidget(self.status)
		self.box.addWidget(self.edit)

