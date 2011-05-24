'''
Copyright (c) 2011, Terrence Cole.
All rights reserved.
'''
from PyQt4.QtCore import QCoreApplication
from PyQt4.QtGui import QTextBrowser
from melano.hl.constant import Constant
from melano.hl.name import Name
from melano.hl.nameref import NameRef
from melano.util.debug import qt_debug

class MpSymbolInfoWidget(QTextBrowser):
	OPERATORS = {
		'<', '<=', '==', '!=', '>', '>=', 'is', 'is not', 'in', 'not in', 'and', 'or' '|=',
		'^=', '&=', '<<=', '>>=', '+=', '-=', '*=', '/=', '//=', '%=', '**=', '*', '**'
	}
	PUNCTUATION = {
		'(', ')', '[', ']', ',',
	}


	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.app = QCoreApplication.instance()
		self.project = self.app.project


	def show_info(self, name, types, attrs, subs):
		out = '<h2>{}</h2>'.format(name)
		if types:
			out += '''
			<h3>Types:</h3>
			<ul>
				{}
			<ul>
			'''.format('\n'.join(types))
		#name=name, types=, attrs='\n'.join(attrs), subs='\n'.join(subs))
		self.setHtml(out)


	def format_attrs(self, attributes):
		return []


	def format_subscripts(self, subscripts):
		return []


	def show_keyword(self, word:str):
		typename = 'Keyword: '
		if word in self.OPERATORS:
			typename = 'Operator: '
		elif word in self.PUNCTUATION:
			typename = 'Punctuation: '
		self.show_info(typename + word, [], [], [])


	def show_constant(self, node:Constant):
		typename = node.type.__class__.__name__
		self.show_info('Constant', [typename], self.format_attrs(node.attributes), self.format_subscripts(node.subscripts))


	def show_symbol(self, node:Name):
		if not node:
			self.setHtml('')
			return

		node = node.deref()

		if node.types:
			typeinfo = ['<li>{}</li>'.format(ty.__class__.__name__) for ty in node.types]
		else:
			typeinfo = ['<li>{}</li>'.format(node.get_type().__class__.__name__)]

		self.show_info(node.name, typeinfo, self.format_attrs(node.attributes), self.format_subscripts(node.subscripts))
