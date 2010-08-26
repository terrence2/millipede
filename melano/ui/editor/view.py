from PyQt4.QtGui import QTextEdit
from .document import MelanoCodeDocument

class MelanoCodeEdit(QTextEdit):
	def __init__(self, parent):
		super().__init__(parent)
	
		self.setTabStopWidth(1)
	
		
