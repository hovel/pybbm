"""
The root of pybb tests.
"""
import unittest

from pybb.tests.postmarkup import PostmarkupTestCase

def suite():
    cases = (PostmarkupTestCase,
            )
    tests = unittest.TestSuite(
        unittest.TestLoader().loadTestsFromTestCase(x)\
        for x in cases)
    return tests
