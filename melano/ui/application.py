from PyQt4.QtGui import QApplication
from melano.config.config import MelanoConfig
from melano.code.symbols.module import Module
from melano.code.symbols.block import Block
from melano.code.symbols.symbol import Symbol
from .main import MelanoMainWindow
from .editor.document import MelanoCodeDocument
import os.path
import base64


class MelanoApplication(QApplication):
	def __init__(self, *args):
		super().__init__(*args)
		
		# create the configuration
		self.config = MelanoConfig()
		self.config.thaw()

		# store loaded documents
		self.documents = {}
	
		# setup icon search paths
		self.icons_dir = os.path.join('.', 'data', 'icons')

		# the main application window
		self.window = MelanoMainWindow()
		self.window.show()
		try:
			w = int(self.config.get_key('app_window_w'))
			h = int(self.config.get_key('app_window_h'))
			x = int(self.config.get_key('app_window_x'))
			y = int(self.config.get_key('app_window_y'))
			winstate = base64.b64decode(self.config.get_key('app_window_state').encode('ascii'))
			self.window.restoreState(winstate)
			self.window.resize(w, h)
			self.window.move(x, y)
		except (KeyError, ValueError):
			pass


	def onQuitTriggered(self):
		data = base64.b64encode(bytes(self.window.saveState()))
		self.config.set_key('app_window_state', data.decode('ascii'))
		sz = self.window.size()
		pos = self.window.pos()
		self.config.set_key('app_window_w', str(sz.width()))
		self.config.set_key('app_window_h', str(sz.height()))
		self.config.set_key('app_window_x', str(pos.x()))
		self.config.set_key('app_window_y', str(pos.y()))
		self.config.freeze()
		self.exit()


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
		
		
