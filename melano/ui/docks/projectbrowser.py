from PyQt4.QtCore import QCoreApplication
from PyQt4.QtGui import QTreeWidget, QTreeWidgetItem, QIcon
from melano.hl.class_ import MelanoClass
from melano.hl.function import MelanoFunction
from melano.hl.module import MelanoModule
from melano.hl.name import Name
import os.path


class MelanoProjectTreeWidget(QTreeWidget):
	TYPE_LOADED = 32
	TYPE_MODULE	 = 33
	TYPE_NODE = 34

	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.project = QCoreApplication.instance().project

		# load icon paths
		#self.ICONS = {
		self.icon_package = QIcon(os.path.join(QCoreApplication.instance().icons_dir, "ide-package.svg"))
		self.icon_module = QIcon(os.path.join(QCoreApplication.instance().icons_dir, "ide-module.svg"))
		self.icon_class = QIcon(os.path.join(QCoreApplication.instance().icons_dir, "ide-class.svg"))
		self.icon_method = QIcon(os.path.join(QCoreApplication.instance().icons_dir, "ide-method.svg"))
		self.icon_function = QIcon(os.path.join(QCoreApplication.instance().icons_dir, "ide-function.svg"))
		self.icon_import = QIcon(os.path.join(QCoreApplication.instance().icons_dir, "ide-import.svg"))
		self.icon_symbol = QIcon(os.path.join(QCoreApplication.instance().icons_dir, "ide-symbol.svg"))
		self.icon_parameter = QIcon(os.path.join(QCoreApplication.instance().icons_dir, "ide-parameter.svg"))
		#}

		self.setColumnCount(1)
		self.setHeaderLabel('Name')

		#self.itemExpanded.connect(self.onItemExpanded)
		self.itemActivated.connect(self.onItemActivated)

		self._setup()

	def _select_icon(self, sym):
		import pdb; pdb.set_trace()
		print('sym:', sym)
		if sym.scope:
			print("scope: ", type(sym.scope))
			if isinstance(sym.scope, MelanoClass):
				return self.icon_class
			elif isinstance(sym.scope, MelanoModule):
				if sym.filename.endswith('__init__.py'):
					return self.icon_package
				else:
					return self.icon_module
			elif isinstance(sym.scope, MelanoFunction):
				return self.icon_function
		return QIcon.fromTheme("emblem-unreadable")

	def _setup(self):
		seen = set()
		def _add_children(item, mod):
			for ref in mod.refs:
				childMod = self.project.get_module_at_filename(ref)
				child = QTreeWidgetItem(item)
				child.setText(0, ref)
				child.setIcon(0, self._select_icon(childMod.owner))
				child.setData(0, self.TYPE_MODULE, childMod)
				child.setData(0, self.TYPE_NODE, None)
				item.addChild(child)
				_add_children(child, childMod)
			for name, sym in mod.symbols.items():
				if not isinstance(sym, Name): continue
				child = QTreeWidgetItem(item)
				child.setText(0, name)
				child.setIcon(0, self._select_icon(sym))
				child.setData(0, self.TYPE_MODULE, mod)
				child.setData(0, self.TYPE_NODE, mod.symbols[name])
				item.addChild(child)


		for prog in self.project.programs:
			mod = self.project.get_module_at_dottedname(prog)
			item = QTreeWidgetItem(self)
			item.setText(0, prog)
			item.setIcon(0, self._select_icon(mod.owner))
			item.setData(0, self.TYPE_MODULE, mod)
			item.setData(0, self.TYPE_NODE, None)
			self.addTopLevelItem(item)
			_add_children(item, mod)

	'''
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
					icon = self.icon_package
				elif node.get_symbol(name).__class__.__name__ == 'Module':
					icon = self.icon_module
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
		'''

	'''
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
				if node.__class__.__name__ == 'Symbol':
					return
				for name in node.get_names():
					child_node = node.get_symbol(name)
					child = QTreeWidgetItem(item)
					child.setText(0, name)
					child.setData(0, self.TYPE_LOADED, True)
					child.setData(0, self.TYPE_MODULE, module)
					child.setData(0, self.TYPE_NODE, node.get_symbol(name))
					icon = self.icon_symbol
					if child_node.__class__.__name__ == 'Class':
						icon = self.icon_class
					elif child_node.__class__.__name__ == 'Function':
						#if node.get_symbol(name).is_method
						icon = self.icon_function
					elif child_node.__class__.__name__ == 'Symbol':
						if child_node.ast_context.__class__.__name__ == 'Import' or \
							child_node.ast_context.__class__.__name__ == 'ImportFrom':
							icon = self.icon_import
						elif child_node.ast_context.__class__.__name__ == 'FunctionDef':
							icon = self.icon_parameter
					child.setIcon(0, icon)
					item.addChild(child)
					_insert_ast_children(child, node.get_symbol(name), module)
			_insert_ast_children(item, module, module)

			# mark us as loaded
			item.setData(0, self.TYPE_LOADED, True)
	'''

	def onItemActivated(self, item:QTreeWidgetItem, col:int):
		module = item.data(0, self.TYPE_MODULE)
		node = item.data(0, self.TYPE_NODE)

		# if we have no module, this is not a document we can open
		if not module:
			return

		# this will on-demand load the document and browse to the symbol
		QCoreApplication.instance().show_symbol(module, node)


