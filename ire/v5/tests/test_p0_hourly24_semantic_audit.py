import unittest
from pathlib import Path
from ire.v5.validation.p0_hourly24_semantic_audit import audit_bundle

class Hourly24SemanticAuditTest(unittest.TestCase):
    def test_real_original_cue_and_provisional_claim_coverage(self):
        path=Path(__file__).resolve().parents[1]/"validation"/"private_source_derived_20261107"/"hourly24_w25_w36.json.zlib.b64"
        r=audit_bundle(path,"98950e51935f58a8affa42b59487ff99351594c4577e21db92c57c6b20a050e3",
            "af4d89d0e69b219947fdf82cdd9f3229c1f7b1e14c05c924ac815d2511f6c531",25,36,432,647)
        self.assertEqual((r["windows"],r["cues"],r["claims"],r["next_window"]),(12,216,38,"W00037"))
        self.assertFalse(r["p0_go"])
    def test_wrong_source_hash_rejected(self):
        path=Path(__file__).resolve().parents[1]/"validation"/"private_source_derived_20261107"/"hourly24_w25_w36.json.zlib.b64"
        with self.assertRaisesRegex(ValueError,"P0_UNVERIFIED_RELEASE"):
            audit_bundle(path,"98950e51935f58a8affa42b59487ff99351594c4577e21db92c57c6b20a050e3","0"*64,25,36,432,647)
if __name__=="__main__":
    unittest.main()
