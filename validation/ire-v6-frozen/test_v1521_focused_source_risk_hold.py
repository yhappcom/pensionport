"""V152.1 SHA-only proof ensures 42 source-first risk notes stay nonapproved."""
from __future__ import annotations
import copy, hashlib, json, unittest
from pathlib import Path

FILE=Path(__file__).with_name("V1521_FOCUSED_42_SOURCE_RISK_SHA_ONLY.json")
EXPECTED="SOURCE_FIRST_FOCUSED_NONBLIND_CHAT_RISK_NOTES__REVISED_HOST_AND_FINAL_V123_OPEN"

def check(summary):
    if not isinstance(summary,dict) or summary.get("schema")!="V1521_FORTY_TWO_SOURCE_FIRST_FOCUSED_MEANING_HOLD_V1":
        raise ValueError("V1521_SCHEMA")
    if summary.get("original_sha256")!="638fefee007aa9122e68717b922194410ebbd7913a619bb9354f09af14468a0d":
        raise ValueError("V1521_OWNER_SOURCE")
    if (type(summary.get("prior_pending_claim_count")) is not int or
        summary["prior_pending_claim_count"]!=202 or
        type(summary.get("focused_source_review_count")) is not int or
        summary["focused_source_review_count"]!=42 or
        type(summary.get("remaining_prior_pending_not_focus_count")) is not int or
        summary["remaining_prior_pending_not_focus_count"]!=160):
        raise ValueError("V1521_COUNT_OR_QUEUE")
    digest=summary.get("focused_review_risks_sha256")
    if not isinstance(digest,str) or len(digest)!=64 or any(c not in "0123456789abcdef" for c in digest):
        raise ValueError("V1521_NOTE_PIN")
    for field in ("focus_high_risk_fn_zero_certified","full_gold_score_certified","p0_go"):
        if summary.get(field) is not False:raise ValueError("V1521_FALSE_GO_"+field)
    for field in ("meaning_approved_through_v123","formal_v128_knowledge_published"):
        if type(summary.get(field)) is not int or summary[field]!=0:raise ValueError("V1521_FALSE_APPROVAL_"+field)
    if summary.get("status")!=EXPECTED:raise ValueError("V1521_STATUS")
    return {"owner_referenced_risk_notes":42,
            "still_pending_final_semantic_adjudication":202,
            "knowledge_published":0,"precision_recall_certified":False,
            "review_not_external_independence":True,"p0e_go":False}

class V1521SourceRisk(unittest.TestCase):
    def setUp(self):
        self.r=json.loads(FILE.read_text(encoding="utf-8"))
    def test_owner_sha_only_no_gold_claim(self):
        self.assertFalse(check(self.r)["p0e_go"])
    def test_no_false_v123_approval(self):
        x=copy.deepcopy(self.r);x["meaning_approved_through_v123"]=42
        with self.assertRaisesRegex(ValueError,"FALSE_APPROVAL"):check(x)
    def test_no_claimed_zero_high_risk_omission(self):
        x=copy.deepcopy(self.r);x["focus_high_risk_fn_zero_certified"]=True
        with self.assertRaisesRegex(ValueError,"FALSE_GO"):check(x)
    def test_no_false_precision_score(self):
        x=copy.deepcopy(self.r);x["full_gold_score_certified"]=True
        with self.assertRaisesRegex(ValueError,"FALSE_GO"):check(x)
    def test_no_fake_risk_note_count(self):
        x=copy.deepcopy(self.r);x["focused_source_review_count"]=202
        with self.assertRaisesRegex(ValueError,"COUNT_OR_QUEUE"):check(x)

if __name__=="__main__":unittest.main()
