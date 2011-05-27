'''
All top-level linting algorithms.
'''
__author__ = 'Terrence Cole <terrence@zettabytestorage.com>'

from .linter_driver import lint
from .reporter import report
__all__ = ('lint', 'report')

