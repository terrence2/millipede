from PyQt4.QtGui import QFrame, QWidget, QHBoxLayout
from millipede.ui.editor.edit import MpCodeEdit
from millipede.ui.editor.document import MpCodeDocument
from millipede.ui.editor.line_status import MpCodeLineStatus


class MpCodeView(QFrame):
	def __init__(self, doc:MpCodeDocument, parent:QWidget):
		super().__init__(parent)
		self.setFrameStyle(QFrame.StyledPanel | QFrame.Sunken)
		self.setLineWidth(2)

		self.edit = MpCodeEdit(doc, self)

		self.status = MpCodeLineStatus(self.edit, self)

		self.box = QHBoxLayout(self)
		self.box.setSpacing(0)
		self.box.setMargin(0)
		self.box.addWidget(self.status)
		self.box.addWidget(self.edit)

