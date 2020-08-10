"""Tests for Sigma Verify tool."""
from __future__ import unicode_literals

import unittest

from sigma_verify_rules import *

class TestSigmaVerifyRules(unittest.TestCase):
    def test_get_code_path(self):
        """Test the get code path function."""
        code_path_output = get_codepath
        logging.info("asd")
        self.assertIsNotNone(code_path_output)

    def test_verify_rules_file(self):
        """Test some of the verify rules code."""

        self.assertFalse(verify_rules_file("foo", "bar", None))
        self.assertFalse(verify_rules_file("../data/sigma/rules/", "../data/sigma_config.yaml", None))
        


if __name__ == '__main__':
    unittest.main()

