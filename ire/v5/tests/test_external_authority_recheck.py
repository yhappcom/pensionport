"""Adversarial tests for original-cue and independently published authority checks.

No original copyrighted SRT goes into repository. Source-content recheck is
optional on a private local ZIP and is not falsely reported as a CI success.
"""
import copy
import unittest
from pathlib import Path
from unittest.mock import patch
from ire.v5 import external_authority_recheck as m

ROOT=Path(__file__).resolve().parents[3]
DIR=ROOT/"ire/v5/advisory_knowledge/verification_20261104"

class ExternalAuthorityRecheckTests(unittest.TestCase):
    def test_real_source_authority_crosscheck(self):
        r=m.verify(ROOT)
        self.assertEqual(r["source_windows_checked"],10)
        self.assertEqual(r["unique_new_study_claims_scoped"],9)
        self.assertEqual(r["new_study_claims_still_unassessed"],44)
        self.assertEqual(r["separately_authored_reference_sources"],14)
        self.assertEqual(r["educational_fact_candidates"],5)
        self.assertEqual(r["conditional_education_only"],1)
        self.assertEqual(r["dated_rule_monitor"],1)
        self.assertEqual(r["held_or_blocked"],3)
        self.assertFalse(r["private_srt_bytes_reverified_during_this_run"])
        self.assertFalse(r["formal_financial_advice_go"])
        self.assertFalse(r["independent_blind_human_evaluation_completed"])

    def altered(self,filename,fn):
        original=m.load
        def replacement(path):
            o=original(path)
            if Path(path).name==filename:
                o=copy.deepcopy(o)
                fn(o)
            return o
        with patch.object(m,"load",side_effect=replacement):
            return m.verify(ROOT)

    def test_invented_video_cue_range_rejected(self):
        with self.assertRaisesRegex(m.IndependentAuthorityGateError,"CUE_ANCHOR_MALFORMED"):
            self.altered("source_spans.json",lambda x:
                         x["rows"][0].update(last_cue=99999))

    def test_claim_id_must_belong_to_original_video(self):
        with self.assertRaisesRegex(m.IndependentAuthorityGateError,
                                    "CUE_ANCHOR_NOT_LINKED_TO_STUDY_CLAIM"):
            self.altered("source_spans.json",lambda x:
                         x["rows"][0].update(source_study_claim_id="A237-05"))

    def test_statute_from_future_invalid(self):
        def edit(x):
            next(r for r in x["sources"] if r["id"]=="REF-ISA-STATUTE-2026")[
                "legal_effective_from"]="2027-01-01"
        with self.assertRaisesRegex(m.IndependentAuthorityGateError,
                                    "LAW_EFFECTIVE_DATE_FUTURE_OR_NONLAW"):
            self.altered("external_authorities.json",edit)

    def test_fake_official_domain_rejected(self):
        with self.assertRaisesRegex(m.IndependentAuthorityGateError,"AUTHORITY_HOST_NOT_APPROVED"):
            self.altered("external_authorities.json",lambda x:
                         x["sources"][0].update(url="https://fake.example.com/law"))

    def test_source_authority_reference_must_exist(self):
        with self.assertRaisesRegex(m.IndependentAuthorityGateError,
                                    "ADJUDICATION_UNGROUNDED_AUTHORITY_REF"):
            self.altered("adjudications.json",lambda x:
                         x["rows"][0].update(authority_ids=["REF-NONEXISTENT"]))

    def test_forged_independent_blind_approval_rejected(self):
        with self.assertRaisesRegex(m.IndependentAuthorityGateError,
                                    "BLIND_REVIEW_OR_ADVICE_APPROVAL_FABRICATED"):
            self.altered("adjudications.json",lambda x:
                         x.update(blind_human_review_completed=True))

    def test_source_based_safe_disposition_cannot_be_overstated(self):
        def edit(x):
            next(r for r in x["rows"] if r["audit_id"]=="P10_DCA_GUARANTEE")[
                "disposition"]="EVIDENCE_SUPPORTED_EDUCATIONAL_SCOPE"
        with self.assertRaisesRegex(m.IndependentAuthorityGateError,
                                    "RELEASE_DISTRIBUTION_NOT_REPRODUCIBLE"):
            self.altered("adjudications.json",edit)

    def test_irp_government_proposal_cannot_become_enacted_effective_date(self):
        def edit(x):
            next(r for r in x["sources"] if r["id"]=="REF-IRP-PROPOSAL-MOEL")[
                "legal_effective_from"]="2026-10-29"
        with self.assertRaisesRegex(m.IndependentAuthorityGateError,
                                    "LAW_EFFECTIVE_DATE_FUTURE_OR_NONLAW"):
            self.altered("external_authorities.json",edit)

    def test_tax_and_asr_safeguards_present(self):
        x=m.load(DIR/"adjudications.json")
        by={r["audit_id"]:r for r in x["rows"]}
        self.assertEqual(by["P02_ISA_RECLASSIFY"]["disposition"],"HOLD_CONTEXT")
        self.assertEqual(by["P06_IRP_70PCT"]["disposition"],"DATED_POLICY_WATCH")
        self.assertEqual(by["P05_PENSION_7PCT"]["disposition"],"BLOCK_UNSAFE_PROJECTION")
        self.assertEqual(by["P10_DCA_GUARANTEE"]["disposition"],"BLOCK_UNSAFE_PROJECTION")
        self.assertIn("영상 자체",by["P04_PENSION_1500"]["critical_limit"])
        self.assertIn("300만원",by["P07_IRP_PENSION_TRANSFER"]["critical_limit"])

if __name__=="__main__":
    unittest.main()
