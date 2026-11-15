"""V124 negative controls; public archived government originals + synthetic case rows."""
import copy
import hashlib
import tempfile
import unittest
from pathlib import Path

from v124_finance12_primary_provenance_guard import (
    CASE_IDS, _case_expected_class, _case_expected_source,
    audit_archived_finance_case_relevance,
)
ROOT = Path(__file__).resolve().parent
RAW = ROOT / "public_official_raw_20261108"

def synthetic_rows():
    return [{
        "reference_id":cid,
        "linked_archived_body_ids":list(_case_expected_source(cid)),
        "original_source_class":_case_expected_class(cid),
        "private_evidence_note_sha256":hashlib.sha256(("synthetic "+cid).encode()).hexdigest(),
        "authority_issuer_checked":False,
        "current_effective_range_verified":False,
        "exact_account_and_product_scope_verified":False,
        "speaker_audio_verified":False,
        "primary_claim_body_entailment_adjudicated":False,
        "finance_fact_status":"OPEN",
        "finance_fact_approved":False,
    } for cid in CASE_IDS]

class V124OriginalBodyAndClaimScope(unittest.TestCase):
    def test_replay_both_original_government_bodies_12_hold(self):
        q=audit_archived_finance_case_relevance(RAW,synthetic_rows())
        self.assertEqual(q["official_archived_original_bodies_sha_verified"],2)
        self.assertEqual(q["finance12_cases_accounted"],12)
        self.assertEqual(q["cases_with_older_archived_law_source_context"],3)
        self.assertEqual(q["cases_with_direct_statutory_subclause_present"],1)
        self.assertEqual(q["cases_without_claim_specific_archived_body"],9)
        self.assertFalse(q["archived_nts_generic_pension_page_has_isa_60_day_proof"])
        self.assertFalse(q["claim_substantive_entailment_approved"])
        self.assertEqual(q["finance_cases_open"],12)
        self.assertEqual(q["status"],"FINANCE12_PRIMARY_BYTES_PARTIAL_SCOPE_HOLD")
        self.assertFalse(q["new_research_candidates_export_allowed"])
    def test_generic_nts_does_not_prove_isa_60_days(self):
        q=synthetic_rows()
        q[9]["linked_archived_body_ids"]=["nts_pension"]
        with self.assertRaisesRegex(ValueError,"IRRELEVANT_OR_MISATTRIBUTED"):
            audit_archived_finance_case_relevance(RAW,q)
    def test_withdrawal_order_does_not_prove_penalty_exemption(self):
        q=synthetic_rows()
        q[6]["original_source_class"]="STATUTORY_SOURCE_ORDER_CLAUSE_ONLY_NOT_CASE_ELIGIBILITY"
        with self.assertRaisesRegex(ValueError,"IRRELEVANT_OR_MISATTRIBUTED"):
            audit_archived_finance_case_relevance(RAW,q)
    def test_issuer_promotion_is_not_statute(self):
        q=synthetic_rows()
        q[10]["linked_archived_body_ids"]=["decree_40_3"]
        with self.assertRaisesRegex(ValueError,"IRRELEVANT_OR_MISATTRIBUTED"):
            audit_archived_finance_case_relevance(RAW,q)
    def test_false_finance_approval_or_scope_assertion_blocked(self):
        for field in ("finance_fact_approved","current_effective_range_verified",
                      "authority_issuer_checked","primary_claim_body_entailment_adjudicated",
                      "speaker_audio_verified"):
            q=synthetic_rows()
            q[7][field]=True
            with self.subTest(field=field),self.assertRaisesRegex(ValueError,"PREMATURE_CLOSURE"):
                audit_archived_finance_case_relevance(RAW,q)
    def test_missing_duplicate_case_denied(self):
        for mutation in (lambda q:q.pop(),lambda q:q.append(copy.deepcopy(q[-1]))):
            q=synthetic_rows()
            mutation(q)
            with self.assertRaisesRegex(ValueError,"CASE_CENSUS"):
                audit_archived_finance_case_relevance(RAW,q)
    def test_forged_original_government_body_denied(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)
            for name in ("capture_manifest.json","decree_40_3.html","nts_pension.html"):
                (p/name).write_bytes((RAW/name).read_bytes())
            (p/"decree_40_3.html").write_bytes(b"forged page")
            with self.assertRaisesRegex(ValueError,"OFFICIAL_RAW_RESPONSE_TAMPERED"):
                audit_archived_finance_case_relevance(p,synthetic_rows())
if __name__=="__main__":
    unittest.main()
