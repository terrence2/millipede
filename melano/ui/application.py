from PyQt4.QtGui import QApplication
from melano.config.config import MelanoConfig
from .main import MelanoMainWindow
from .editor.document import MelanoCodeDocument
import os.path


class MelanoApplication(QApplication):
	def __init__(self, *args):
		super().__init__(*args)
		self.config = MelanoConfig()
		self.documents = {}
	
		# setup icon search paths
		self.icons_dir = os.path.join('.', 'data', 'icons')

		self.window = MelanoMainWindow()
		self.window.show()


	def load_document(self, module):

		# load the document
		doc = self.documents.get(module.get_filename())
		if not doc:
			doc = MelanoCodeDocument(module, self.window)
			self.documents[module.get_filename()] = doc

		# find out if we have a view for this document
		self.window.show_document(doc)
		return doc
