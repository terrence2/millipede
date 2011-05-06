from .editor.document import MelanoCodeDocument
from .main import MelanoMainWindow
from PyQt4.QtGui import QApplication
from melano.hl.module import MelanoModule
from melano.hl.name import Name
import base64
import os.path
#from melano.config.config import MelanoConfig
#from melano.code.symbols.module import Module
#from melano.code.symbols.block import Block
#from melano.code.symbols.symbol import Symbol


class MelanoApplication(QApplication):
	def __init__(self, project, *args):
		super().__init__(*args)
		self.project = project

		# store loaded documents
		self.documents = {}

		# setup icon search paths
		self.icons_dir = os.path.join('.', 'data', 'icons')

		# the main application window
		self.window = MelanoMainWindow()
		self.window.show()

		self.window.resize(800, 600)

		'''
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
		'''

	def onQuitTriggered(self):
		'''
		data = base64.b64encode(bytes(self.window.saveState()))
		self.config.set_key('app_window_state', data.decode('ascii'))
		sz = self.window.size()
		pos = self.window.pos()
		self.config.set_key('app_window_w', str(sz.width()))
		self.config.set_key('app_window_h', str(sz.height()))
		self.config.set_key('app_window_x', str(pos.x()))
		self.config.set_key('app_window_y', str(pos.y()))
		self.config.freeze()
		'''
		self.exit()


	def load_document(self, module:MelanoModule):
		# load the document
		doc = self.documents.get(module.filename)
		if not doc:
			doc = MelanoCodeDocument(module, self.window)
			self.documents[module.filename] = doc

		return doc


	def view_closed(self, filename:str):
		del self.documents[filename]


	def show_symbol(self, module:MelanoModule, node:Name):
		doc = self.load_document(module)
		self.window.show_symbol(doc, node)


	def on_hover_text(self, module:MelanoModule, start:(int, int), end:(int, int), context:str):
		'''Discover the node we are hovering over based on the position of the token.  Possibly 
			format and return a tooltip if this is possible for this text position.'''
		#module.find_ast_node_for_position
		return 'Hover Text!'

