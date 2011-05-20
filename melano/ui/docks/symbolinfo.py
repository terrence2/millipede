'''
Copyright (c) 2011, Terrence Cole.
All rights reserved.
'''
from PyQt4.QtCore import QCoreApplication
from PyQt4.QtGui import QTextBrowser
from melano.hl.name import Name
from melano.util.debug import qt_debug

class MpSymbolInfoWidget(QTextBrowser):
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.app = QCoreApplication.instance()
		self.project = self.app.project



	def show_symbol(self, node:Name):
		typeinfo = '\n'.join(['<li>{}</li>'.format(str(ty)) for ty in node.types])
		data = '''
		<h2>{node.name}</h2>
		<h3>Types</h3>
		<ul>
			{types}
		<ul>
		'''.format(node=node, types=typeinfo)
		#node.name
		#node.types
		#node.attributes
		#node.subscripts

		self.setHtml(data)

		#qt_debug()
		#print(node)
