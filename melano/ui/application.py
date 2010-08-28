from PyQt4.QtGui import QApplication
from melano.config.config import MelanoConfig
from melano.code.symbols.module import Module
from melano.code.symbols.block import Block
from melano.code.symbols.symbol import Symbol
from .main import MelanoMainWindow
from .editor.document import MelanoCodeDocument


class MelanoApplication(QApplication):
	def __init__(self, *args):
		super().__init__(*args)
		self.config = MelanoConfig()
		self.documents = {}
	
		self.window = MelanoMainWindow()
		self.window.show()


	def load_document(self, module:Module):
		# load the document
		doc = self.documents.get(module.get_filename())
		if not doc:
			doc = MelanoCodeDocument(module, self.window)
			self.documents[module.get_filename()] = doc
		
		return doc
	
	
	def view_closed(self, filename:str):
		del self.documents[filename]
	
	
	def show_symbol(self, module:Module, node:Block or Symbol):
		doc = self.load_document(module)
		view = self.window.show_document(doc)
		view.show_symbol(node)
		
		
