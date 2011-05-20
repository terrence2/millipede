from PyQt4.QtCore import QCoreApplication
from PyQt4.QtGui import QListWidget, QListWidgetItem


class MpProjectListWidget(QListWidget):
	def __init__(self, *args):
		super().__init__(*args)
		self.config = QCoreApplication.instance().config

		project_names = self.config.get_project_names()
		for name in project_names:
			QListWidgetItem(name, self)

		self.itemActivated.connect(self.onItemActivated)


	def onItemActivated(self, item:QListWidgetItem):
		self.config.log.info("Selected project: %s", item.text())
		self.config.set_project(item.text())


