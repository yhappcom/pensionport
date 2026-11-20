"""V205 E1 fail-fast preflight regression tests."""
import unittest
from v205_e1_runtime_preflight import (
    find_testcase_run_override,validate_e1_test_runtime)


class TestV205E1Preflight(unittest.TestCase):
    def test_detect_shadowed_unittest_run_before_work(self):
        malicious='''import unittest
class FragileTest(unittest.TestCase):
    def run(self, **kwargs):
        return True
'''
        self.assertEqual(find_testcase_run_override(malicious),
                         ["FragileTest.run"])

    def test_legitimate_test_method_not_misclassified(self):
        okay='''from unittest import TestCase
class TestOkay(TestCase):
    def test_01(self):
        self.assertTrue(True)
'''
        self.assertEqual(find_testcase_run_override(okay),[])

    def test_all_e1_tests_satisfy_runtime_preflight(self):
        result=validate_e1_test_runtime()
        self.assertEqual(result["preflight"],"PASS")
        self.assertEqual(result["unittest_run_overrides"],0)
        self.assertGreaterEqual(result["e1_test_files_checked"],5)


if __name__=="__main__":
    unittest.main()
