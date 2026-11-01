"""Post-seal legacy 260-video comparison cannot contaminate new IRE facts."""
from __future__ import annotations
import json
import subprocess
import sys
import tempfile
from pathlib import Path
import unittest
from ire.source import sha256
from ire.knowledge import empty_knowledge,ingest_new_video,save_private_snapshot
from ire.v2_legacy_delta import post_seal_legacy_delta
from test_engine import VID,synthetic_srt
from test_knowledge import make_report

OTHER="Qq12345AbCd"


class LegacySeparationV2Tests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.home=Path(self.temp.name)
        self.original,digest=synthetic_srt()
        report=make_report(self.original,VID,self.home/"source_session")
        self.new=ingest_new_video(empty_knowledge(),self.original,report)
        self.before=self.new["snapshot_sha256"]
        self.old={
            "schema":"IRE_LEGACY_QUARANTINED_CLAIMS_V1",
            "claims":[
                {"legacy_claim_id":"LEGACY_001","video_id":VID,
                 "claim_text":"해당 상품의 비용이 계약 조건에 따라 달라질 수 있다.",
                 "historical_status":"LEGACY_NOT_GOLD_UNVERIFIED"},
                {"legacy_claim_id":"LEGACY_002","video_id":VID,
                 "claim_text":"여름철 과일을 채소처럼 취급하는 이야기",
                 "historical_status":"LEGACY_NOT_GOLD_UNVERIFIED"},
                {"legacy_claim_id":"LEGACY_003","video_id":OTHER,
                 "claim_text":"다른 영상에서 제기된 금융 투자 원칙 이야기",
                 "historical_status":"LEGACY_NOT_GOLD_UNVERIFIED"}
            ]
        }

    def test_compare_only_after_new_source_sealed_and_cannot_import_legacy(self):
        result=post_seal_legacy_delta(self.new,self.old)
        self.assertEqual(result["legacy_claims_reviewed"],3)
        self.assertEqual(result["legacy_claims_imported_as_fact_or_gold"],0)
        self.assertFalse(result["new_ire_knowledge_modified"])
        self.assertEqual(self.new["snapshot_sha256"],self.before)
        self.assertFalse(result[
            "historical_comparison_eligible_for_advisory_without_recheck"])
        self.assertEqual(result["legacy_difference_queue"][-1][
            "comparison_status"],"NEW_ORIGINAL_NOT_YET_STUDIED")
        self.assertEqual(result["legacy_difference_queue"][0][
            "comparison_status"],"POST_SEAL_SIMILARITY_REVIEW_ONLY")
        text=json.dumps(result,ensure_ascii=False)
        self.assertNotIn("여름철 과일을",text)
        self.assertNotIn("해당 상품의 비용이",text)
        self.assertIn("POSSIBLE_NEW_IRE_OMISSION_REQUIRES_SOURCE_RECHECK",
                      text)

    def test_unsealed_knowledge_refuses_legacy_comparison(self):
        with self.assertRaisesRegex(ValueError,
                                    "LEGACY_COMPARISON_REQUIRES_FROZEN_NEW_IRE_WORK"):
            post_seal_legacy_delta(empty_knowledge(),self.old)

    def test_duplicate_legacy_id_and_forged_gold_label_refused(self):
        erroneous=json.loads(json.dumps(self.old))
        erroneous["claims"][1]["legacy_claim_id"]="LEGACY_001"
        with self.assertRaisesRegex(ValueError,
                                    "LEGACY_ENTRY_ID_DUPLICATED_OR_INVALID"):
            post_seal_legacy_delta(self.new,erroneous)
        erroneous=json.loads(json.dumps(self.old))
        erroneous["claims"][0]["historical_status"]="VERIFIED_FINANCIAL_FACT"
        with self.assertRaisesRegex(ValueError,
                                    "LEGACY_UNTRUSTED_STUDY_INPUT_INVALID"):
            post_seal_legacy_delta(self.new,erroneous)

    def test_legacy_cli_private_report_never_copies_old_study_into_knowledge(self):
        snapshot=save_private_snapshot(self.new,str(self.home/"knowledge"))
        legacy=self.home/"private_legacy.json"
        legacy.write_text(json.dumps(self.old,ensure_ascii=False))
        result=self.home/"private_differences.json"
        p=subprocess.run([
            sys.executable,"-m","ire.v2_legacy_delta",
            "--private-new-knowledge",str(snapshot),
            "--private-legacy-manifest",str(legacy),
            "--private-difference-report",str(result)],
            text=True,capture_output=True,check=False)
        self.assertEqual(p.returncode,2,p.stderr+p.stdout)
        public=json.loads(p.stdout)
        self.assertEqual(public["imported_historical_fact_count"],0)
        self.assertTrue(result.is_file())
        self.assertEqual(result.stat().st_mode & 0o077,0)
        self.assertEqual(self.new["snapshot_sha256"],self.before)
        self.assertNotIn("여름철 과일을",p.stdout)


if __name__=="__main__":
    unittest.main()
