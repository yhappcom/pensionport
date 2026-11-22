"""P0-0-06 security integrity/privilege adversarial tests (not source-secrecy GO)."""
from __future__ import annotations

import base64
import copy
import json
import unittest
import zlib

from scripts.ire_security_archive_gate import (
    ROOT,INVENTORY,V3,V5,B64,AuditError,
    blob_sha,sha256,validate_manifest,inspect,parse_reversible_b64,
    parse_v5_readme,
)

class ArchiveSecurityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.original=json.loads((ROOT/INVENTORY).read_text(encoding="utf-8"))

    def setUp(self):
        self.item=copy.deepcopy(self.original)

    def expected_bad(self,code):
        with self.assertRaises(AuditError) as cm:
            validate_manifest(ROOT,self.item)
        self.assertEqual(cm.exception.code,code)

    def test_01_all_42_actual_repositories_scan_without_leaking_values(self):
        found=inspect(ROOT,self.item)
        self.assertEqual(found["integrity_verdict"],"PASS_42_HASHED_ARCHIVES_AND_REVERSED_B64")
        self.assertEqual(found["totals"][V3],25)
        self.assertEqual(found["totals"][V5],11)
        self.assertEqual(found["totals"][B64],6)
        self.assertFalse(found["private_source_exposure_absence_certified"])

    def test_02_same_real_archive_scan_never_claims_decryption(self):
        found=inspect(ROOT,self.item)
        self.assertEqual(found["security_release"],"HOLD")
        self.assertEqual(found["actual_v3_v5_decryption"],"NOT_VERIFIED_NO_KEY")
        self.assertTrue(found["public_b64_reversible"])

    def test_03_v3_archive_hash_tamper_rejected(self):
        row=next(x for x in self.item["files"] if x["group"]==V3)
        row["sha256"]="0"*64
        self.expected_bad("PPC1_SHA_MISMATCH")

    def test_04_v5_archive_hash_tamper_rejected(self):
        row=next(x for x in self.item["files"] if x["group"]==V5)
        row["sha256"]="0"*64
        self.expected_bad("V5_ARCHIVE_SHA_MISMATCH")

    def test_05_cannot_drop_one_packed_file(self):
        self.item["files"].pop()
        self.expected_bad("FILE_INVENTORY_NOT_42")

    def test_06_cannot_duplicate_archive_path(self):
        self.item["files"][1]["path"]=self.item["files"][0]["path"]
        self.expected_bad("DUPLICATE_SECURITY_FILES")

    def test_07_cannot_relabel_public_b64_as_encrypted(self):
        row=next(x for x in self.item["files"] if x["group"]==B64)
        row["group"]=V3
        self.expected_bad("SECURITY_GROUP_COUNT_DRIFT")

    def test_08_false_release_eligible_is_blocked(self):
        self.item["files"][-1]["release_eligible"]=True
        self.expected_bad("ARCHIVE_HOLD_OR_ACCESS_LAUNDERED")

    def test_09_claiming_key_recovery_without_key_is_blocked(self):
        self.item["actual_decryption_and_restore_proved"]=True
        self.expected_bad("FALSE_CONFIDENTIALITY_OR_RECOVERY")

    def test_10_claiming_no_private_exposure_is_blocked(self):
        self.item["private_data_exposure_absence_certified"]=True
        self.expected_bad("FALSE_CONFIDENTIALITY_OR_RECOVERY")

    def test_11_pinned_source_head_cannot_be_forged(self):
        self.item["source_snapshot_sha"]="a"*40
        self.expected_bad("INVENTORY_SOURCE_SHA")

    def test_12_public_packed_content_cannot_be_called_a_cipher(self):
        row=next(x for x in self.item["files"] if x["group"]==B64)
        row["current_risk"]="PASS"
        self.expected_bad("ARCHIVE_HOLD_OR_ACCESS_LAUNDERED")

    def test_13_reversible_base64_test_fixture_only_counters(self):
        data={"source_text":"한국어 발화에 관한 비공개 내용이 아니라 합성 시험 문장"*3,
              "details":[{"note":"synthetic high risk classification context"}]}
        raw=json.dumps(data,ensure_ascii=False).encode("utf-8")
        encoded=base64.b64encode(zlib.compress(raw))
        counts=parse_reversible_b64(encoded)
        self.assertEqual(counts["decoded_bytes"],len(raw))
        self.assertGreater(counts["korean_text"],0)
        self.assertGreater(counts["semantic_text"],0)
        self.assertNotIn("source_text",counts)
        self.assertNotIn("details",counts)

    def test_14_bad_base64_blocked(self):
        with self.assertRaisesRegex(AuditError,"INVALID_BASE64"):
            parse_reversible_b64(b"bad??")

    def test_15_corrupt_zlib_blocked(self):
        with self.assertRaisesRegex(AuditError,"B64_CORRUPT_JSON_OR_ZLIB"):
            parse_reversible_b64(base64.b64encode(b"not zlib"))

    def test_16_trailing_bytes_after_zlib_blocked(self):
        encoded=base64.b64encode(zlib.compress(b"{}")+b"trailing")
        with self.assertRaisesRegex(AuditError,"B64_TRAILING_OR_INCOMPLETE_ZLIB"):
            parse_reversible_b64(encoded)

    def test_17_trailing_json_nonjson_rejected(self):
        encoded=base64.b64encode(zlib.compress(b'{"secret_data":"x"')
        )
        with self.assertRaisesRegex(AuditError,"B64_CORRUPT_JSON_OR_ZLIB"):
            parse_reversible_b64(encoded)

    def test_18_decompression_zip_bomb_limited(self):
        zipbomb=base64.b64encode(zlib.compress(b"A"*8_100_000))
        with self.assertRaisesRegex(AuditError,"B64_DECOMPRESSION_SIZE_LIMIT"):
            parse_reversible_b64(zipbomb)

    def test_19_plain_json_scalar_is_not_complete_source(self):
        encoded=base64.b64encode(zlib.compress(b'"scalar"'))
        with self.assertRaisesRegex(AuditError,"B64_JSON_NOT_OBJECT_OR_ARRAY"):
            parse_reversible_b64(encoded)

    def test_20_path_traversal_rejected(self):
        self.item["files"][0]["path"]="../../research/original.srt"
        self.expected_bad("INVENTORY_TRAVERSAL")

    def test_21_metadata_upstream_blob_pins(self):
        self.item["v3_manifest_git_blob_sha1"]="0"*40
        self.expected_bad("V3_MANIFEST_CHANGED")

    def test_22_mismatched_v5_readme_census(self):
        row=next(x for x in self.item["files"] if x["group"]==V5)
        row["path"]="ire/v5/encrypted_archives/UNKNOWN.v5enc"
        self.expected_bad("V5_ARCHIVE_SHA_MISMATCH")

    def test_23_current_source_inventory_has_25_plus_11_plus_6(self):
        paths=[x["path"] for x in self.item["files"]]
        self.assertEqual(len(paths),len(set(paths)))
        self.assertEqual(len(paths),42)
        validate_manifest(ROOT,self.item)

    def test_24_no_crypto_or_text_leak_from_digest_math(self):
        self.assertRegex(blob_sha(b"synthetic"),r"^[0-9a-f]{40}$")
        self.assertRegex(sha256(b"synthetic"),r"^[0-9a-f]{64}$")


if __name__=="__main__":
    unittest.main()
