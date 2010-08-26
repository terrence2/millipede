from PyQt4 import QtCore
from PyQt4.QtCore import QCoreApplication
from PyQt4.QtGui import QMainWindow
from PyQt4.QtGui import QAction, QIcon, QLabel, QDockWidget, QTreeView
from melano.ui.editor.view import MelanoCodeEdit
from melano.ui.editor.document import MelanoCodeDocument
from melano.ui.docks.projectlist import MelanoProjectListWidget
from melano.ui.docks.projectbrowser import MelanoProjectTreeWidget


class MelanoMainWindow(QMainWindow):
	def __init__(self):
		super().__init__()

		self.codeview = MelanoCodeEdit(self)
		self.setCentralWidget(self.codeview)

		self.actionQuit = QAction(QIcon.fromTheme("application-exit"), "&Quit", self)
		self.actionQuit.triggered.connect(self.onQuitTriggered)

		self.fileMenu = self.menuBar().addMenu("&File")
		self.fileMenu.addAction(self.actionQuit)
		#self.fileMenu.addAction(openAct)
		#self.fileMenu.addAction(saveAct)

		self.projectsList = MelanoProjectListWidget(self)
		self.dockProjectList = QDockWidget("Project List", self)
		self.dockProjectList.setAllowedAreas(QtCore.Qt.LeftDockWidgetArea | QtCore.Qt.RightDockWidgetArea)
		self.dockProjectList.setWidget(self.projectsList)
		self.addDockWidget(QtCore.Qt.LeftDockWidgetArea, self.dockProjectList)

		self.projectBrowser = MelanoProjectTreeWidget(self)
		self.dockProjectTree = QDockWidget("Project Browser", self);
		self.dockProjectTree.setAllowedAreas(QtCore.Qt.LeftDockWidgetArea | QtCore.Qt.RightDockWidgetArea);
		self.dockProjectTree.setWidget(self.projectBrowser)
		self.addDockWidget(QtCore.Qt.LeftDockWidgetArea, self.dockProjectTree)



	def onQuitTriggered(self):
		QCoreApplication.exit()

	
	def show_document(self, doc:MelanoCodeDocument):
		self.codeview.setDocument(doc)


