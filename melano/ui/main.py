from PyQt4 import QtCore
from PyQt4.QtGui import QMainWindow
from PyQt4.QtGui import QLabel, QDockWidget, QTreeView
from melano.ui.codeedit import MelanoCodeEdit
from melano.ui.docks.projectlist import MelanoProjectListWidget
from melano.ui.docks.projectbrowser import MelanoProjectTreeWidget

class MelanoMainWindow(QMainWindow):
	def __init__(self):
		super().__init__()

		self.codeview = MelanoCodeEdit(self)


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

		'''		
		self.toolsLayout = QVBoxLayout(self)
		self.toolsLayout.addWidget(QLabel("Hello", self))
		self.toolsWidget = QWidget(self)
		self.toolsWidget.setLayout(self.toolsLayout)
		
		
		self.splitter = QSplitter(QtCore.Qt.Horizontal, self)
		self.splitter.addWidget(self.toolsWidget)
		self.splitter.addWidget(self.codeview)
		'''
		
		
		self.setCentralWidget(self.codeview)
