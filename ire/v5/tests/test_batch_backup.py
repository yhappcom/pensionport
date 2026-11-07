"""Cross-store encrypted 5-video batch roundtrip and tamper tests."""
import tempfile
import unittest
from pathlib import Path
from ire.v5.batch import FiveVideoResearchBatch
from ire.v5.batch_backup import export_batch, restore_batch
from ire.v5.tests.test_batch import fixture_video
from ire.v5.engine import RunError

class MultiBackupTests(unittest.TestCase):
 def setUp(self):
  t=tempfile.TemporaryDirectory();self.addCleanup(t.cleanup)
  self.base=Path(t.name)
  self.batch=FiveVideoResearchBatch("five-video-backup",[fixture_video(i) for i in range(1,6)],self.base/"original")
  self.archive=self.base/"batch.v5pack"
  self.secret="synthetic_secure_password_five_videos_only"
 def test_restore_sources_and_replay_independent(self):
  e=export_batch(self.batch,self.secret,self.archive)
  self.assertEqual(e["video_count"],5)
  x=restore_batch(self.archive,self.secret,self.base/"recovered")
  self.assertTrue(x["fresh_store_replay_verified"])
  original=self.batch.status()
  restored=FiveVideoResearchBatch.open_private(self.base/"recovered").status()
  self.assertEqual(restored,original)
  self.assertNotIn(b"Pension scenario",self.archive.read_bytes())
 def test_wrong_key_does_not_restore_partial_source(self):
  export_batch(self.batch,self.secret,self.archive)
  with self.assertRaises(RunError):
   restore_batch(self.archive,"incorrect_recovery_passphrase",self.base/"recovered")
  self.assertFalse((self.base/"recovered").exists())
 def test_tampered_archive_denied(self):
  export_batch(self.batch,self.secret,self.archive)
  b=bytearray(self.archive.read_bytes());b[-40]^=5;self.archive.write_bytes(b)
  with self.assertRaises(Exception):restore_batch(self.archive,self.secret,self.base/"recovered")
  self.assertFalse((self.base/"recovered").exists())
 def test_existing_destination_denied(self):
  export_batch(self.batch,self.secret,self.archive)
  with self.assertRaisesRegex(RunError,"FIVE_VIDEO_ARCHIVE_WOULD_OVERWRITE"):
   export_batch(self.batch,self.secret,self.archive)
  restore_batch(self.archive,self.secret,self.base/"recovered")
  with self.assertRaisesRegex(RunError,"FIVE_VIDEO_RESTORE_WOULD_OVERWRITE"):
   restore_batch(self.archive,self.secret,self.base/"recovered")
if __name__=="__main__":unittest.main()
