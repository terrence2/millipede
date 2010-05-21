#!/usr/bin/python3
'''
Run all tests.
'''
__author__ = 'Terrence Cole <terrence@zettabytestorage.com>'

import os.path
import sys
sys.path = [os.path.realpath('.')] + sys.path

from melano.test.tests import *

if __name__ == '__main__':
    import logging
    import unittest

    logging.basicConfig()

    unittest.main()

