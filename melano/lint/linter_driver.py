'''
Aggregate and call all lint sub-programs on a unit.
'''
__author__ = 'Terrence Cole <terrence@zettabytestorage.com>'

from .fluff import annotations
from .fluff import docstrings

def lint(unit):
	'''Perform linting of one unit.'''
	msgs = []
	msgs.extend(annotations.analyse(unit))
	msgs.extend(docstrings.analyse(unit))
	return msgs


