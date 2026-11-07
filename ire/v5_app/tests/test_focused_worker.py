"""Public V5 focused summary contract tests; synthetic identifiers only."""
import unittest
from ire.v5_app.focused_worker import SCHEMA,project

class FocusedStatusTests(unittest.TestCase):
    def test_schema_is_stable(self):
        self.assertEqual(SCHEMA,"IRE_V5_64_PUBLIC_CHECKPOINT_V1")

if __name__=="__main__":
    unittest.main()
