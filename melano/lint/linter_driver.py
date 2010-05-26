'''
Aggregate and call all lint sub-programs on a unit.
'''
__author__ = 'Terrence Cole <terrence@zettabytestorage.com>'

from .fluff import annotations

def lint(unit):
	'''Perform linting of one unit.'''
	msgs = []
	msgs.extend(annotations.analyse(unit))
	return msgs


