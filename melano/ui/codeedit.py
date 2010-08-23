from PyQt4.QtGui import QTextEdit
from melano.ui.codedocument import MelanoCodeDocument

class MelanoCodeEdit(QTextEdit):
	def __init__(self, parent):
		super().__init__(parent)
	
		self.setTabStopWidth(4)
	
		self.doc = MelanoCodeDocument(self)
		self.setDocument(self.doc)
		
