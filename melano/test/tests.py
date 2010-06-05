'''
Unittest needs to be spoon-fed the list of tests.
'''
__author__ = 'Terrence Cole <terrence@zettabytestorage.com>'

from melano.parser.test.test_parse import TestParse
from melano.lint.fluff.test.test_annotations import TestLintAnnotations
from melano.lint.fluff.test.test_docstrings import TestLintDocstrings
from melano.lint.fluff.test.test_methodargs import TestLintMethodArgs
from melano.lint.fluff.test.test_classinit import TestLintClassInit
from melano.lint.fluff.test.test_generator import TestLintGenerator

