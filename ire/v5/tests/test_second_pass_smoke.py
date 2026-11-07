"""Fail-closed public smoke checks for second-pass historic relation reconciliation."""
import unittest
from ire.v5.second_pass import SCHEMA,EV_SCHEMA,RelationSecondPass
from ire.v5.second_pass_backup import SCHEMA as BACKUP_SCHEMA,restore

class SecondPassImportTests(unittest.TestCase):
    def test_explicit_schema(self):
        self.assertEqual(SCHEMA,"IRE_V5_SECOND_PASS_RELATION_V1")
        self.assertEqual(EV_SCHEMA,"IRE_V5_SECOND_PASS_EVENT_V1")
        self.assertEqual(BACKUP_SCHEMA,"IRE_V5_SECOND_PASS_COMBINED_ARCHIVE_V1")
    def test_recovery_requires_real_archive(self):
        with self.assertRaises(FileNotFoundError):
            restore(archive=__import__("pathlib").Path("/nonexistent-v5-bundle"),passphrase="not a valid run",destination=__import__("pathlib").Path("/nonexistent-v5-target"))
    def test_no_public_model_entrypoint(self):
        self.assertFalse(hasattr(RelationSecondPass,"invoke_external_model"))
