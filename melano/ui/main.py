from PyQt4 import QtCore
from PyQt4.QtCore import QCoreApplication
from PyQt4.QtGui import QMainWindow
from PyQt4.QtGui import QAction, QIcon, QLabel, QDockWidget, QTreeView, QTabWidget
from melano.ui.editor.view import MelanoCodeEdit
from melano.ui.editor.document import MelanoCodeDocument
from melano.ui.docks.projectlist import MelanoProjectListWidget
from melano.ui.docks.projectbrowser import MelanoProjectTreeWidget
import os.path


class MelanoMainWindow(QMainWindow):
	def __init__(self):
		super().__init__()

		# one MelanoCodeEdit for each view in the tabwidget
		self.views = {}

		# the core widget is a tabpane
		self.tabPane = QTabWidget()
		self.tabPane.setDocumentMode(True)
		self.tabPane.setMovable(True)
		self.tabPane.setTabsClosable(True)
		self.tabPane.tabCloseRequested.connect(self.onTabCloseRequested)
		self.setCentralWidget(self.tabPane)

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


	def onTabCloseRequested(self, index:int):
		view = self.tabPane.widget(index)
		self.tabPane.removeTab(index)
		del self.views[view.document().filename]
		QCoreApplication.instance().view_closed(view.document().filename)
	
	
	def show_document(self, doc:MelanoCodeDocument):
		if doc.filename in self.views:
			self.tabPane.setCurrentWidget(self.views[doc.filename])
			return self.views[doc.filename]
		
		self.views[doc.filename] = MelanoCodeEdit(None)
		self.views[doc.filename].setDocument(doc)
		self.tabPane.addTab(self.views[doc.filename], QIcon.fromTheme("text-x-generic"), os.path.basename(doc.filename))
		self.tabPane.setCurrentIndex(self.tabPane.count() - 1)

		return self.views[doc.filename]

