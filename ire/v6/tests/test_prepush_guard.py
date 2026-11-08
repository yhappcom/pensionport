"""Portable prepush tests: never assume the tests run outside a full Git repo."""
from pathlib import Path
import tempfile
import unittest

from ire.v6.prepush import run, _check_full_checkout


class PrepushGuardTests(unittest.TestCase):
    def test_full_repo_gate_blocks_partial_source_checkout(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root/"ire/v6").mkdir(parents=True)
            (root/"ire/v6/store.py").write_text("# synthetic incomplete source\n")
            result = run(root, strict=True,
                expected_sha="f753ba57a1afabaa849f3eeca88170938c0b51f6")
            self.assertEqual(result["outcome"], "BLOCKED_PREPUSH_VALIDATION")
            self.assertIn("REQUIRED_REPO_FILE_MISSING", result["reason"])
            self.assertIn("GIT_CHECKOUT_REQUIRED", result["reason"])
            self.assertFalse(result["engine_quality_certified"])
            self.assertEqual(result["checks"], [])

    def test_isolated_validation_is_distinct_from_strict_prepush(self):
        with tempfile.TemporaryDirectory() as tmp:
            reasons, sha = _check_full_checkout(Path(tmp), None)
            self.assertIn("GIT_CHECKOUT_REQUIRED", reasons)
            self.assertIsNone(sha)
            self.assertIn("EXACT_CANONICAL_HEAD_SHA_REQUIRED", reasons)


if __name__=="__main__":
    unittest.main()
