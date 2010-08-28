from PyQt4.QtCore import QCoreApplication
from PyQt4.QtGui import QTreeWidget, QTreeWidgetItem, QIcon


class MelanoProjectTreeWidget(QTreeWidget):
	TYPE_LOADED = 32
	TYPE_MODULE	 = 33
	TYPE_NODE = 34

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

		def _insert_db_children(item, node):
			for name in node.get_names():
				child = QTreeWidgetItem(item)
				child.setText(0, name)
				child.setData(0, self.TYPE_LOADED, True)
				child.setData(0, self.TYPE_MODULE, None)
				icon = QIcon.fromTheme("package-x-generic")
				if node.get_symbol(name).__class__.__name__ == 'Package':
					icon = QIcon.fromTheme("package-x-generic")
				elif node.get_symbol(name).__class__.__name__ == 'Module':
					icon = QIcon.fromTheme("application-x-executable")
					placeholder = QTreeWidgetItem(child)
					placeholder.setText(0, "loading...")
					placeholder.setIcon(0, QIcon.fromTheme("process-working"))
					child.addChild(placeholder)
					child.setData(0, self.TYPE_LOADED, False)
					child.setData(0, self.TYPE_MODULE, node.get_symbol(name))
					child.setData(0, self.TYPE_NODE, node.get_symbol(name))
				child.setIcon(0, icon)
				item.addChild(child)
				_insert_db_children(child, node.get_symbol(name))
		
		project = self.config.get_project()
		for name in project.db.get_names():
			item = QTreeWidgetItem(self)
			item.setText(0, name)
			item.setIcon(0, QIcon.fromTheme("package-x-generic"))
			self.addTopLevelItem(item)
			_insert_db_children(item, project.db.get_symbol(name))


	def onItemExpanded(self, item:QTreeWidgetItem):
		module = item.data(0, self.TYPE_MODULE)
		if not module:
			return
		
		if not item.data(0, self.TYPE_LOADED):
			# clean out the item
			while item.childCount() > 0:
				child = item.child(0)
				item.removeChild(child)
			
			# on-demand load the ast
			module.get_node()
			
			# load all children
			def _insert_ast_children(item, node, module):
				if node.__class__.__name__ == 'Name':
					return
				for name in node.get_names():
					child = QTreeWidgetItem(item)
					child.setText(0, name)
					child.setData(0, self.TYPE_LOADED, True)
					child.setData(0, self.TYPE_MODULE, module)
					child.setData(0, self.TYPE_NODE, node)
					icon = QIcon.fromTheme("package-x-generic")
					if node.get_symbol(name).__class__.__name__ == 'Class':
						icon = QIcon.fromTheme("package-x-generic")
					elif node.get_symbol(name).__class__.__name__ == 'Function':
						icon = QIcon.fromTheme("package-x-generic")
					elif node.get_symbol(name).__class__.__name__ == 'Symbol':
						icon = QIcon.fromTheme("package-x-generic")
					child.setIcon(0, icon)
					item.addChild(child)
					_insert_ast_children(child, node.get_symbol(name), module)
			_insert_ast_children(item, module, module)
			
			# mark us as loaded
			item.setData(0, self.TYPE_LOADED, True)
			
		
		print("expanded")


	def onItemActivated(self, item:QTreeWidgetItem, col:int):
		module = item.data(0, self.TYPE_MODULE)
		if not module:
			return
		
		# load and display the document
		doc = QCoreApplication.instance().load_document(module)
		
		#FIXME: span to the spot in the document corresponding the the symbol we activated
		
		
		print("activated", doc)


