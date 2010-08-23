from PyQt4.QtGui import QApplication
from melano.config.config import MelanoConfig

class MelanoApplication(QApplication):
	def __init__(self, *args):
		super().__init__(*args)
		self.config = MelanoConfig()
