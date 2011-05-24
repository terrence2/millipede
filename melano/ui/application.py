from .editor.document import MpCodeDocument
from .main import MpMainWindow
from PyQt4.QtGui import QApplication
from melano.hl.constant import Constant
from melano.hl.module import MpModule
from melano.hl.name import Name
from melano.ui.visitors.node_position_mapper import NodePositionMapper
from melano.util.debug import qt_debug
import base64
import os.path


class MpApplication(QApplication):
	def __init__(self, project, *args):
		super().__init__(*args)
		self.project = project

		# store loaded documents
		self.documents = {}

		# setup icon search paths
		self.icons_dir = os.path.join('.', 'data', 'icons')

		# the main application window
		self.window = MpMainWindow()
		self.window.show()

		self.window.resize(800, 600)

		# keep a map of positions -> hl nodes, for documents we access
		self.nodemap = {}

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


	def load_document(self, module:MpModule):
		# load the document
		doc = self.documents.get(module.filename)
		if not doc:
			doc = MpCodeDocument(module, self.window)
			self.documents[module.filename] = doc

		return doc


	def view_closed(self, filename:str):
		del self.documents[filename]


	def show_symbol(self, module:MpModule, node:Name):
		doc = self.load_document(module)
		self.window.show_symbol(doc, node)


	def on_hover_text(self, module:MpModule, start:(int, int), end:(int, int), context:str):
		'''Discover the node we are hovering over based on the position of the token.  Possibly 
			format and return a tooltip if this is possible for this text position.'''
		#module.find_ast_node_for_position
		return 'Hover Text!'


	def on_click_text(self, module:MpModule, position:(int, int), word:str):
		'''Discover and return the node corresponding to the text symbol we clicked on.  Take an appropriate action
			based on the type of the token.'''
		if module.filename not in self.nodemap:
			visitor = NodePositionMapper()
			visitor.visit(module.ast)
			self.nodemap[module.filename] = visitor.out

		def pos_to_word():
			for start, end, hl in self.nodemap[module.filename]:
				if start[0] <= position[0] and end[0] >= position[0]:
					if start[1] <= position[1] and end[1] >= position[1]:
						return hl
			return None
		node = pos_to_word()

		if node:
			if isinstance(node, Constant):
				self.window.symInfo.show_constant(node)
			else:
				self.window.symInfo.show_symbol(node)
		else:
			self.window.symInfo.show_keyword(word)

		#qt_debug()

