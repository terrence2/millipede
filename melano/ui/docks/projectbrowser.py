from PyQt4.QtCore import QCoreApplication
from PyQt4.QtGui import QTreeWidget, QTreeWidgetItem, QIcon


class MelanoProjectTreeWidget(QTreeWidget):
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.config = QCoreApplication.instance().config
		self.config.projectChanged.connect(self.onProjectChanged)
	
		self.setColumnCount(1)
		self.setHeaderLabel('Name')

		self.itemExpanded.connect(self.onItemExpanded)
		self.itemActivated.connect(self.onItemActivated)

	
	def onProjectChanged(self, project_name):
		self.clear()

		def _insert_children(item, node):
			for name in node.get_names():
				child = QTreeWidgetItem(item)
				child.setText(0, name)
				if node.get_symbol(name).__class__.__name__ == 'Package':
					icon = QIcon.fromTheme("package-x-generic")
				elif node.get_symbol(name).__class__.__name__ == 'Module':
					icon = QIcon.fromTheme("application-x-executable")
					placeholder = QTreeWidgetItem(child)
					placeholder.setText(0, "loading...")
					child.addChild(placeholder)
					child.setData(0, 32, node.get_symbol(name))
				child.setIcon(0, icon)
				item.addChild(child)
				_insert_children(child, node.get_symbol(name))
				
		
		project = self.config.get_project()
		for name in project.db.get_names():
			item = QTreeWidgetItem(self)
			item.setText(0, name)
			item.setIcon(0, QIcon.fromTheme("package-x-generic"))
			self.addTopLevelItem(item)
			_insert_children(item, project.db.get_symbol(name))


	def onItemExpanded(self, item:QTreeWidgetItem):
		print("expanded")

	def onItemActivated(self, item:QTreeWidgetItem, col:int):
		node = item.data(0, 32)
		if not node:
			return
			
		print("activated", node)


