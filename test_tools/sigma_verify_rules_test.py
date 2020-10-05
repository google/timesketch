"""Tests for Sigma Verify tool."""
from __future__ import unicode_literals

import unittest

from sigma_verify_rules import get_codepath, verify_rules_file, run_verifier

class TestSigmaVerifyRules(unittest.TestCase):
    def test_get_code_path(self):
        """Test the get code path function."""
        code_path_output = get_codepath
        self.assertIsNotNone(code_path_output)

    def test_verify_rules_file(self):
        """Test some of the verify rules code."""

        self.assertFalse(verify_rules_file("foo", "bar", None))
        self.assertFalse(verify_rules_file("../data/sigma/rules/",
        "../data/sigma_config.yaml", None))

    def test_run_verifier(self):
        self.assertRaises(IOError, run_verifier, 
        '../data/sigma_config.yaml', '../data/sigma/rules/')

        config = './data/sigma_config.yaml'
        rules = './data/sigma/rules/'

        sigma_verified_rules, sigma_rules_with_problems = run_verifier(config_file_path=config, rules_path=rules)
        
        found = False
        for verified_rule in sigma_verified_rules:
            if 'lnx_susp_zenmap' in verified_rule:
                found = True
        
        self.assertTrue(found)
        
if __name__ == '__main__':
    unittest.main()
