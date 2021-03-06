from PyQt4 import QtCore
from PyQt4.QtCore import QCoreApplication
from PyQt4.QtGui import QAction, QIcon, QLabel, QDockWidget, QTreeView, \
	QTabWidget, QMainWindow
from millipede.hl.nodes.name import Name
from millipede.ui.docks.projectbrowser import MpProjectTreeWidget
from millipede.ui.docks.projectlist import MpProjectListWidget
from millipede.ui.docks.symbolinfo import MpSymbolInfoWidget
from millipede.ui.editor.document import MpCodeDocument
from millipede.ui.editor.view import MpCodeView
import os.path


class MpMainWindow(QMainWindow):
	def __init__(self):
		super().__init__()

		# one MpCodeEdit for each view in the tabwidget
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

		'''
		self.projectsList = MpProjectListWidget(self)
		self.dockProjectList = QDockWidget("Project List", self)
		self.dockProjectList.setObjectName('dockProjectList')
		self.dockProjectList.setAllowedAreas(QtCore.Qt.LeftDockWidgetArea | QtCore.Qt.RightDockWidgetArea)
		self.dockProjectList.setWidget(self.projectsList)
		self.addDockWidget(QtCore.Qt.LeftDockWidgetArea, self.dockProjectList)
		'''

		self.projectBrowser = MpProjectTreeWidget(self)
		self.dockProjectTree = QDockWidget("Project Browser", self);
		self.dockProjectTree.setObjectName('dockProjectTree')
		self.dockProjectTree.setAllowedAreas(QtCore.Qt.LeftDockWidgetArea | QtCore.Qt.RightDockWidgetArea);
		self.dockProjectTree.setWidget(self.projectBrowser)
		self.addDockWidget(QtCore.Qt.LeftDockWidgetArea, self.dockProjectTree)


		self.symInfo = MpSymbolInfoWidget(self)
		self.dockSymInfo = QDockWidget("Symbol Info", self);
		self.dockSymInfo.setObjectName('dockSymbolInfo')
		self.dockSymInfo.setAllowedAreas(QtCore.Qt.LeftDockWidgetArea | QtCore.Qt.RightDockWidgetArea);
		self.dockSymInfo.setWidget(self.symInfo)
		self.addDockWidget(QtCore.Qt.RightDockWidgetArea, self.dockSymInfo)


	def closeEvent(self, *args):
		QCoreApplication.instance().onQuitTriggered()


	def onQuitTriggered(self):
		QCoreApplication.instance().onQuitTriggered()


	def onTabCloseRequested(self, index:int):
		view = self.tabPane.widget(index)
		self.tabPane.removeTab(index)
		del self.views[view.edit.document().filename]
		QCoreApplication.instance().view_closed(view.edit.document().filename)


	def show_document(self, doc:MpCodeDocument):
		# show and return the existing view
		if doc.filename in self.views:
			self.tabPane.setCurrentWidget(self.views[doc.filename])
			return self.views[doc.filename]

		# create a new view and tab for the view
		self.views[doc.filename] = MpCodeView(doc, None)
		self.tabPane.addTab(self.views[doc.filename], QIcon.fromTheme("text-x-generic"), os.path.basename(doc.filename))
		self.tabPane.setCurrentIndex(self.tabPane.count() - 1)

		return self.views[doc.filename]


	def show_symbol(self, doc:MpCodeDocument, node:Name):
		view = self.show_document(doc)
		view.edit.show_symbol(node)

		self.projectBrowser.show_symbol(node)
		self.symInfo.show_symbol(node)

